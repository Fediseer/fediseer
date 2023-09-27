from fediseer.apis.v1.base import *
from fediseer import enums
from fediseer.faq import FEDISEER_FAQ

class FAQ(Resource):

    get_parser = reqparse.RequestParser()
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    get_parser.add_argument("category", required=False, type=str, help="If provided, will only return entries from that category", location="args")


    @api.expect(get_parser)
    @api.marshal_with(models.response_model_faq_entry, code=200, description='FAQ Entries', as_list=True)
    @api.response(400, 'Bad Request', models.response_model_error)

    def get(self):
        '''Retrieve FAQ answers
        '''
        self.args = self.get_parser.parse_args()
        if not self.args.category:
            return FEDISEER_FAQ,200
        filtered_faq = []
        all_categories = set()
        for entry in FEDISEER_FAQ:
            all_categories.add(entry["category"])
            if entry["category"] == self.args.category:
                filtered_faq.append(entry)
        if len(filtered_faq) == 0:
            raise e.BadRequest(f"Category not known. Please choose from: {all_categories}")
        return filtered_faq,200
