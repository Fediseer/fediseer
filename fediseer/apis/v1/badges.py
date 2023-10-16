from fediseer.apis.v1.base import *
from fediseer.badges import generate_endorsements_badge, generate_guarantee_badge
from sqlalchemy.orm import aliased
from fediseer.classes.instance import Guarantee, Endorsement
from flask import make_response
from sqlalchemy import func
from fediseer import enums

class GuaranteeBadge(Resource):

    def get(self, domain):
        '''Retrieve Guarantee Badge SVG
        '''
        guaranteed_instance_alias = aliased(Instance)
        query = db.session.query(
            Instance.domain, 
            guaranteed_instance_alias.domain,
        ).join(
            Guarantee, Instance.id == Guarantee.guaranteed_id
        ).join(
            guaranteed_instance_alias, guaranteed_instance_alias.id == Guarantee.guarantor_id
        ).filter(
            Instance.domain == domain
        )
        guarantor = query.first()
        if guarantor is None:
            svg = generate_guarantee_badge(domain, None)
        else:
            svg = generate_guarantee_badge(domain, guarantor[1])
        response = make_response(svg)
        response.headers['Content-Type'] = 'image/svg+xml'
        return response

class EndorsementBadge(Resource):
    get_parser = reqparse.RequestParser()
    get_parser.add_argument("Client-Agent", default="unknown:0:unknown", type=str, required=False, help="The client name and version.", location="headers")
    get_parser.add_argument("style", required=False, default=enums.BadgeStyle.FULL.name, type=str, help=f"The style the text should take. 'FULL' (default) means icon, text and counter. 'ICON' means just icon and counter.", location="args")

    @api.expect(get_parser)
    def get(self, domain):
        '''Retrieve Endorsement Badge SVG
        '''
        self.args = self.get_parser.parse_args()
        style = enums.BadgeStyle[self.args.style]
        query = db.session.query(
            Instance.domain,
            func.count(Endorsement.id)  # Count the number of endorsements
        ).join(
            Endorsement, Instance.id == Endorsement.endorsed_id
        ).filter(
            Instance.domain == domain
        ).group_by(
            Instance.domain
        )
        endorsements = query.first()
        if endorsements is None:
            svg = generate_endorsements_badge(domain, 0, style)
        else:
            svg = generate_endorsements_badge(domain, endorsements[1], style)
        response = make_response(svg)
        response.headers['Content-Type'] = 'image/svg+xml'
        return response
