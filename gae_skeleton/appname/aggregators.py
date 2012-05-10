#!/usr/bin/env python
#
# Copyright 2012 Ezox Systems LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Logic to handle batching and applying of updates to our tag stats."""

import json
from decimal import Decimal

from google.appengine.ext import ndb
from google.appengine.api import taskqueue

import webapp2

PERIOD_MAP = {
    0: 'o',
    4: 'y',
    6: 'm',
    8: 'd',
    10: 'h'
}

class TagStats(ndb.Model):
    """Stats about Tag entities."""
    period = ndb.StringProperty('p')
    period_type = ndb.ComputedProperty(
        lambda self: PERIOD_MAP.get(len(self.period), 'e'), name='pt')

    tag = ndb.StringProperty('t')

    stats = ndb.JsonProperty('s')
    index = ndb.JsonProperty('i')


class WorkBatcherHandler(webapp2.RequestHandler):
    def post(self):
        """Bundle up work and apply it to our TagStats entity."""
        queue = taskqueue.Queue('work-groups')
        work = queue.lease_tasks_by_tag(30, 500)
        if not work:
            return

        # Go look for more stuff to do.
        taskqueue.add(
            queue_name='default',
            url='/_ah/task/batcher'
        )

        # Process the work we've got.
        apply_work(work)
        queue.delete_tasks(work)


@ndb.transactional
def apply_work(work):
    """Apply the work units to the TagStats entity.

    Note: all work must belong to the same aggregation set.
    """
    if not work:
        return

    tag = work[0].tag

    stat_model_keys, payloads = _parse_work_tasks(work)

    root_stat_key = stat_model_keys[0]

    stat_models = dict(
        (key, model) for key, model in zip(stat_model_keys,
                                           ndb.get_multi(stat_model_keys)))

    root_model = _get_model(root_stat_key, stat_models)

    for unit in payloads:
        amount = Decimal(unit['amount'])

        check_model_key = unit['stat_keys'].pop()
        check_model = _get_model(check_model_key, stat_models)

        entity_key = ndb.Key(urlsafe=unit['entity'])
        last_rev, value = check_model.index.get(entity_key.id(), (None, '0'))
        if last_rev >= unit.get('rev', 0):
            continue

        new = False
        if last_rev is None:
            new = True

        check_model.index[entity_key.id()] = (unit['rev'], str(amount))
        delta = amount - Decimal(value)

        _update_stats(root_model.stats, delta, new)
        _update_stats(check_model.stats, delta, new)

        for key in unit['stat_keys']:
            model = _get_model(key, stat_models)
            _update_stats(model.stats, delta, new)

    ndb.put_multi(stat_models.values())


def _update_stats(stats, amount, new):
    """Update a stats collection."""
    stats['n'] += new
    stats['s'] = str(Decimal(stats['s']) + amount)

def _parse_work_tasks(work):
    """Parse the work tasks and return stat_model_keys and payloads."""
    tag = work[0].tag
    payload = json.loads(work[0].payload)

    root_stat_key = ndb.Key(TagStats, tag, namespace=payload['namespace'])

    stat_model_keys = set()
    payloads = []
    for unit in work:
        payload = json.loads(unit.payload)
        payloads.append(payload)

        keys = []
        for group in [4, 6, 8, 10]:
            stat_key = ndb.Key(TagStats, payload['date'][:group], parent=root_stat_key)
            stat_model_keys.add(stat_key)
            keys.append(stat_key)
        payload['stat_keys'] = keys

    return (root_stat_key,) + tuple(stat_model_keys), payloads


def _get_model(key, models):
    """Fetch a model from the dict of models, if it doesn't
    exist create one and add it to the dict.
    """
    stat_model = models.get(key)
    if stat_model:
        return stat_model

    # The tag is the root entity's key id.
    tag = key.pairs()[0][1]

    # If this is a non-root entity, the period is the key id.
    period = key.id() if key.parent() else ''

    stat_model = TagStats(
        key=key,
        tag=tag,
        period=period)
    models[key] = stat_model

    # Initialize the stats entity.
    stat_model.stats = {
        'n': 0,
        's': Decimal('0.00'),
    }
    stat_model.index = {}

    return stat_model
