from fediseer.apis.v1.base import *
from fediseer import enums

class Report(Resource):

    get_parser = reqparse.RequestParser()
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    get_parser.add_argument("source_domains_csv", required=False, default=None, type=str, help="A csv of source domains for which to filter", location="args")
    get_parser.add_argument("target_domains_csv", required=False, default=None, type=str, help="A csv of target domains for which to filter", location="args")
    get_parser.add_argument("report_type", required=False, default=None, type=str, help="The activity of report to filer ([ADD,DELETE,MODIFY])", location="args")
    get_parser.add_argument("report_activity", required=False, default=None, type=str, help="The activity of report to filer ([GUARANTEE,ENDORSEMENT,CENSURE,RESTRICTION])", location="args")

    @api.expect(get_parser)
    @api.marshal_with(models.response_model_reports, code=200, description='Report', as_list=True)
    @api.response(400, 'Validation Error', models.response_model_error)
    def get(self,page=1):
        '''Retrieve instance information via API Key at 10 results per page
        '''
        self.args = self.get_parser.parse_args()
        source_domains = None
        if self.args.source_domains_csv:
            source_domains = self.args.source_domains_csv.split(',')
        target_domains = None
        if self.args.target_domains_csv:
            target_domains = self.args.target_domains_csv.split(',')
        report_type = None
        if self.args.report_type:
            report_type = enums.ReportType(self.args.report_type)
        report_activity = None
        if self.args.report_activity:
            report_activity = enums.ReportActivity(self.args.report_activity)
        reports = database.get_reports(
            source_instances = source_domains,
            target_instances = target_domains,
            report_type=report_type,
            report_activity=report_activity,
            page=page,
        )
        return reports,200
