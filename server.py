from flask import Flask, request
from flask_restful import Resource, Api
from flask_celery import make_celery

import json, ipdb, os, shelve, uuid

app = Flask(__name__)
api = Api(app)

# Celery config
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
celery = make_celery(app)

@celery.task()
def create_or_update_resource(resource):
    path = os.path.join("resources", resource['id'])
    f = open(path, 'w')
    json.dump(resource, f)
    f.close()

class WellsFargoExercise(Resource):
    def post(self, resource_id=None):
        """
        Handles both the creation and updating of a record.
        If no resource_id is specified we assume creation mode,
        and generate a string identifier for a new record using the
        uuid functionality in the stdlib.
        """
        if resource_id == None: # are we creating a new one?
            resource_id = str(uuid.uuid4())
        
        obj = request.json
        obj['id'] = resource_id

        task = create_or_update_resource.delay(obj)
        task.wait() # Normally you wouldn't do this, but since the API requirements are that the object gets returned after save, we wait.

        return obj

    def get(self, resource_id=None):
        """
        Handles both retrieving a specific record, and listing
        all available records. If no resource_id is specified then
        we assume list mode.
        
        If a requested record doesn't exist, we return a blank
        object rather than a 404.
        """
        if resource_id:
            path = os.path.join("resources", resource_id)
            if not os.path.exists(path): return {}
            return json.load(open(path))
        
        return [x for x in db.values()]

api.add_resource(WellsFargoExercise, "/resources", "/resources/<resource_id>")

if __name__ == "__main__":
    app.debug = True
    app.run()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
