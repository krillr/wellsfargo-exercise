from flask import Flask, request
from flask_restful import Resource, Api
from flask_celery import make_celery

import json, pymongo, uuid

app = Flask(__name__)
api = Api(app)

# Celery config
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
celery = make_celery(app)

mongo = pymongo.MongoClient()
db = mongo.wellsfargo

@celery.task()
def create_or_update_resource(resource):
    db_obj = { "_id": resource['id'], "object": resource }
    db.resources.update({ "_id": resource['id']}, db_obj, upsert=True);

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
        task.wait()

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
	    obj = db.resources.find_one({"_id":resource_id})
            if obj == None: return {}
            return obj['object']
        
        return [x['object'] for x in db.resources.find()]

    def delete(self, resource_id=None):
        """
        Handles both deletion of a single record, and clearing of the
        entire database. If no resource_id is specified, we clear the database.
        """

        if resource_id:
            db.resources.delete_one({"_id":resource_id})
        else:
            db.resources.delete_many({})

	return { "success": True }


api.add_resource(WellsFargoExercise, "/resources", "/resources/<resource_id>")

if __name__ == "__main__":
    app.debug = True
    app.run()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
