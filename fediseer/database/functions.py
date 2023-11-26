from loguru import logger
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_, not_, Boolean
from fediseer.flask import db
from fediseer.utils import hash_api_key
from sqlalchemy.orm import joinedload
from fediseer.classes.instance import Instance, Endorsement, Guarantee, RejectionRecord, Censure, Hesitation, Solicitation, InstanceFlag, InstanceTag, Rebuttal
from fediseer.classes.user import Claim, User
from fediseer.classes.reports import Report
from fediseer import enums

def get_all_instance_query(
        min_endorsements = 0, 
        min_guarantors = 1, 
        tags = None,
        software = None,
        include_decommissioned = True,
    ):
    query = db.session.query(
        Instance
    ).outerjoin(
        Instance.endorsements,
        Instance.guarantors,
    ).options(
        joinedload(Instance.guarantors),
        joinedload(Instance.endorsements),
        joinedload(Instance.admins),
        joinedload(Instance.guarantors),
        joinedload(Instance.tags)
    ).group_by(
        Instance.id
    ).filter(
        or_(
            Instance.oprhan_since == None,
            Instance.oprhan_since > datetime.utcnow() - timedelta(hours=24)
        )
    ).having(
        db.func.count(Instance.endorsements) >= min_endorsements,
    ).having(
        db.func.count(Instance.guarantors) >= min_guarantors,
    )
    if tags:
        # Convert tags to lowercase and filter instances that have any of the tags
        lower_tags = [tag.lower() for tag in tags]
        query = query.filter(Instance.tags.any(func.lower(InstanceTag.tag).in_(lower_tags)))
    if software:
        lower_sw = [sw.lower() for sw in software]
        query = query.filter(Instance.software.in_(lower_sw))
    return query

def get_all_instances(
        min_endorsements = 0, 
        min_guarantors = 1, 
        tags = None,
        software = None,
        include_decommissioned = True,
        page=1,
        limit=10,
    ):
    query = get_all_instance_query(
        min_endorsements = min_endorsements, 
        min_guarantors = min_guarantors, 
        tags = tags,
        software = software,
        include_decommissioned = include_decommissioned,
    )    
    page -= 1
    if page < 0:
        page = 0
    return query.order_by(Instance.created.desc()).offset(limit * page).limit(limit).all()

def count_all_instances(
        min_endorsements = 0, 
        min_guarantors = 1, 
        tags = None,
        software = None,
        include_decommissioned = True,
    ):
    query = get_all_instance_query(
        min_endorsements = min_endorsements, 
        min_guarantors = min_guarantors, 
        tags = tags,
        software = software,
        include_decommissioned = include_decommissioned,
    )    
    return query.count()

def query_all_endorsed_instances_by_approving_id(approving_ids):
    return db.session.query(
        Instance
    ).outerjoin(
        Instance.endorsements,
    ).options(
        joinedload(Instance.endorsements),
    ).filter(
        Endorsement.approving_id.in_(approving_ids)
    ).group_by(
        Instance.id
    )

def count_all_endorsed_instances_by_approving_id(approving_ids):
    query = query_all_endorsed_instances_by_approving_id(approving_ids)
    return query.count()

def get_all_endorsed_instances_by_approving_id(approving_ids,page=1,limit=100):
    query = query_all_endorsed_instances_by_approving_id(approving_ids)
    if limit is not None:
        page -= 1
        if page < 0:
            page = 0
        return query.order_by(Instance.domain).offset(limit * page).limit(limit).all()
    else:
        return query.all()

def get_all_approving_instances_by_endorsed_id(endorsed_id):
    query = db.session.query(
        Instance
    ).outerjoin(
        Instance.approvals,
    ).options(
        joinedload(Instance.approvals),
        joinedload(Instance.endorsements),
        joinedload(Instance.admins),
        joinedload(Instance.guarantors)
    ).filter(
        Endorsement.endorsed_id == endorsed_id
    ).group_by(
        Instance.id
    )
    return query.all()

def get_all_endorsement_reasons_for_endorsed_id(endorsed_id, approving_ids):
    query = Endorsement.query.filter(
        Endorsement.endorsed_id == endorsed_id,
        Endorsement.approving_id.in_(approving_ids),
    ).with_entities(
        Endorsement.reason,
    )
    return query.all()

def get_all_endorsements_from_approving_id(approving_ids):
    query = Endorsement.query.filter(
        Endorsement.approving_id.in_(approving_ids)
    )
    return query.all()



def query_all_censured_instances_by_censuring_id(censuring_ids):
    return db.session.query(
        Instance
    ).outerjoin(
        Instance.censures_received,
    ).options(
        joinedload(Instance.censures_received),
        joinedload(Instance.endorsements),
        joinedload(Instance.approvals),
        joinedload(Instance.admins),
        joinedload(Instance.guarantors)
    ).filter(
        Censure.censuring_id.in_(censuring_ids)
    ).group_by(
        Instance.id
    )

def count_all_censured_instances_by_censuring_id(censuring_ids):
    query = query_all_censured_instances_by_censuring_id(censuring_ids)
    return query.count()

def get_all_censured_instances_by_censuring_id(censuring_ids,page=1,limit=100):
    query = query_all_censured_instances_by_censuring_id(censuring_ids)
    if limit is not None:
        page -= 1
        if page < 0:
            page = 0
        return query.order_by(Instance.domain).offset(limit * page).limit(limit).all()
    else:
        return query.all()

def get_all_censuring_instances_by_censured_id(censured_id):
    query = db.session.query(
        Instance
    ).outerjoin(
        Instance.censures_given,
    ).options(
        joinedload(Instance.censures_given),
    ).filter(
        Censure.censured_id == censured_id
    ).group_by(
        Instance.id
    )
    return query.all()

def get_all_censure_reasons_for_censured_id(censured_id, censuring_ids):
    query = Censure.query.filter(
        Censure.censured_id == censured_id,
        Censure.censuring_id.in_(censuring_ids),
    ).with_entities(
        Censure.censuring_id,
        Censure.reason,
        Censure.evidence,
    )
    return query.all()

def get_all_censures_from_censuring_id(censuring_ids):
    query = Censure.query.filter(
        Censure.censuring_id.in_(censuring_ids)
    )
    return query.all()


def query_all_dubious_instances_by_hesitant_id(hesitant_ids):
    return db.session.query(
        Instance
    ).outerjoin(
        Instance.hesitations_received,
    ).options(
        joinedload(Instance.hesitations_received),
        joinedload(Instance.endorsements),
        joinedload(Instance.approvals),
        joinedload(Instance.admins),
        joinedload(Instance.guarantors)
    ).filter(
        Hesitation.hesitant_id.in_(hesitant_ids)
    ).group_by(
        Instance.id
    )

def count_all_dubious_instances_by_hesitant_id(hesitant_ids):
    query = query_all_dubious_instances_by_hesitant_id(hesitant_ids)
    return query.count()

def get_all_dubious_instances_by_hesitant_id(hesitant_ids,page=1,limit=100):
    query = query_all_dubious_instances_by_hesitant_id(hesitant_ids)
    if limit is not None:
        page -= 1
        if page < 0:
            page = 0
        return query.order_by(Instance.domain).offset(limit * page).limit(limit).all()
    else:
        return query.all()

def get_all_hesitant_instances_by_dubious_id(dubious_id):
    query = db.session.query(
        Instance
    ).outerjoin(
        Instance.hesitations_given,
    ).options(
        joinedload(Instance.hesitations_given),
    ).filter(
        Hesitation.dubious_id == dubious_id
    ).group_by(
        Instance.id
    )
    return query.all()

def get_all_hesitation_reasons_for_dubious_id(dubious_id, hesitant_ids):
    query = Hesitation.query.filter(
        Hesitation.dubious_id == dubious_id,
        Hesitation.hesitant_id.in_(hesitant_ids),
    ).with_entities(
        Hesitation.hesitant_id,
        Hesitation.reason,
        Hesitation.evidence,
    )
    return query.all()

def get_all_hesitations_from_hesitant_id(hesitant_ids):
    query = Hesitation.query.filter(
        Hesitation.hesitant_id.in_(hesitant_ids)
    )
    return query.all()

def get_rebuttal(target_instance_id, source_instance_id):
    query = Rebuttal.query.filter_by(
        target_id=target_instance_id,
        source_id=source_instance_id,
    )
    return query.first()

def get_all_rebuttals_from_source_instance_id(source_instance_id, target_ids = None):
    query = Rebuttal.query.filter(
        Rebuttal.source_id == source_instance_id,
    ).with_entities(
        Rebuttal.rebuttal,
        Rebuttal.target_id,
    )
    if target_ids is not None:
        query = query.filter(Rebuttal.target_id.in_(target_ids))
    return query.all()

def get_all_guaranteed_instances_by_guarantor_id(guarantor_id):
    query = db.session.query(
        Instance
    ).outerjoin(
        Instance.guarantors,
    ).options(
        joinedload(Instance.guarantors),
    ).filter(
        Guarantee.guarantor_id == guarantor_id
    ).group_by(
        Instance.id
    )
    return query.all()

def get_all_guarantor_instances_by_guaranteed_id(guaranteed_id):
    query = db.session.query(
        Instance
    ).outerjoin(
        Instance.guarantees,
    ).options(
        joinedload(Instance.guarantees),
    ).filter(
        Guarantee.guaranteed_id == guaranteed_id
    ).group_by(
        Instance.id
    )
    return query.all()


def find_instance_by_api_key(api_key):
    instance = Instance.query.join(
        Claim
    ).join(
        User
    ).filter(
        User.api_key == hash_api_key(api_key)
    ).first()
    return instance

def find_instance_by_user(user):
    instance = Instance.query.join(
        Claim
    ).join(
        User
    ).filter(
        User.id == user.id
    ).first()
    return instance

def find_instance_by_account(user_account):
    instance = Instance.query.join(
        Claim
    ).join(
        User
    ).filter(
        User.account == user_account
    ).first()
    return instance

def find_instance_by_domain(domain):
    instance = Instance.query.filter_by(domain=domain).first()
    return instance

def find_admins_by_instance(instance):
    users = User.query.join(
        Claim
    ).join(
        Instance
    ).filter(
        Instance.id == instance.id
    ).all()
    return users

def find_claim(admin_username):
    claim = Claim.query.join(
        User
    ).filter(
        User.account == admin_username
    ).first()
    return claim

def find_user_by_api_key(api_key):
    user = User.query.filter(
        User.api_key == hash_api_key(api_key)
    ).first()
    return user

def find_user_by_account(user_account):
    user = User.query.filter(
        User.account == user_account
    ).first()
    return user

def find_instance_by_domain(domain):
    instance = Instance.query.filter_by(domain=domain).first()
    return instance

def find_multiple_instance_by_domains(domains):
    instance = Instance.query.filter(
        Instance.domain.in_(domains)
    ).all()
    return instance

def find_authenticated_instance(domain,api_key):
    instance = Instance.query.join(
        Claim
    ).join(
        User
    ).filter(
        User.api_key == hash_api_key(api_key),
        Instance.domain ==domain,
    ).first()
    return instance

def get_endorsement(instance_id, endorsing_instance_id):
    query = Endorsement.query.filter_by(
        endorsed_id=instance_id,
        approving_id=endorsing_instance_id,
    )
    return query.first()

def get_censure(instance_id, censuring_instance_id):
    query = Censure.query.filter_by(
        censured_id=instance_id,
        censuring_id=censuring_instance_id,
    )
    return query.first()

def get_hesitation(instance_id, hesitant_instance_id):
    query = Hesitation.query.filter_by(
        dubious_id=instance_id,
        hesitant_id=hesitant_instance_id,
    )
    return query.first()

def has_recent_endorsement(instance_id):
    query = Endorsement.query.filter(
        Endorsement.endorsed_id == instance_id,
        Endorsement.created > datetime.utcnow() - timedelta(hours=1),
    )
    return query.first()

def count_endorsements(instance_id):
    query = Endorsement.query.filter_by(
        endorsed_id=instance_id
    )
    return query.count()

def has_recent_rejection(instance_id, rejector_id):
    query = RejectionRecord.query.filter_by(
        rejected_id=instance_id,
        rejector_id=rejector_id,
    ).filter(
        RejectionRecord.performed > datetime.utcnow() - timedelta(hours=24)
    )
    return query.count() > 0

def get_rejection_record(rejector_id, rejected_id):
    query = RejectionRecord.query.filter_by(
        rejected_id=rejected_id,
        rejector_id=rejector_id,
    )
    return query.first()

def get_guarantee(instance_id, guarantor_id):
    query = Guarantee.query.filter_by(
        guaranteed_id=instance_id,
        guarantor_id=guarantor_id,
    )
    return query.first()

def get_guarantor_chain(instance_id):
    guarantors = set()
    chainbreaker = None
    query = Guarantee.query.filter_by(
        guaranteed_id=instance_id,
    )
    guarantor = query.first()
    if not guarantor:
        return set(),instance_id
    guarantors.add(guarantor.guarantor_id)
    if guarantor.guarantor_id != 0:
        higher_guarantors, chainbreaker = get_guarantor_chain(guarantor.guarantor_id)
        guarantors = higher_guarantors | guarantors
    return guarantors,chainbreaker

def has_unbroken_chain(instance_id):
    guarantors, chainbreaker = get_guarantor_chain(instance_id)
    if chainbreaker:
        chainbreaker = Instance.query.filter_by(id=chainbreaker).first()
    return 0 in guarantors,chainbreaker

def get_guarantee_chain(instance_id):
    query = Guarantee.query.filter_by(
        guarantor_id=instance_id,
    )
    guarantees = query.all()
    if not guarantees:
        return set()
    guarantees_ids = set([g.guaranteed_id for g in guarantees])
    for gid in guarantees_ids:
        guarantees_ids = guarantees_ids | get_guarantee_chain(gid)
    return guarantees_ids

def get_instances_by_ids(instance_ids):
    query = Instance.query.filter(
        Instance.id.in_(instance_ids)
    )
    return query

def get_reports(
        source_instances: list = None,
        target_instances: list = None,
        report_type: enums.ReportType = None,
        report_activity: enums.ReportActivity = None,
        page: int = 1,
    ):
    query = Report.query
    if source_instances is not None and len(source_instances) > 0:
        query = query.filter(Report.source_domain.in_(source_instances)
    )
    if target_instances is not None and len(target_instances) > 0:
        query = query.filter(Report.target_domain.in_(target_instances)
    )
    if report_type is not None:
        query = query.filter(Report.report_type == report_type.name
    )
    if report_activity is not None:
        query = query.filter(Report.report_activity == report_activity.name
    )

    page -= 1
    if page < 0:
        page = 0
    return query.order_by(Report.created.desc()).offset(10 * page).limit(10).all()


def get_all_solicitations():
    # Subquery to find the minimum created date for each source_instance
    subq = db.session.query(
        Solicitation.source_id,
        func.min(Solicitation.created).label('oldest_solicitation_date')
    ).group_by(
        Solicitation.source_id
    ).subquery()

    # Query to retrieve instances with at least one solicitation
    query = db.session.query(
        Instance,
    ).join(
        subq,
        Instance.id == subq.c.source_id
    ).filter(
        # We do not show offline instances for solicitation
        Instance.poll_failures < enums.InstanceState.OFFLINE.value
    ).order_by(
        subq.c.oldest_solicitation_date
    )
    
    return query.all()

def find_solicitation_by_target(source_id, target_id):
    query = db.session.query(
        Solicitation
    ).filter(
        Solicitation.source_id == source_id,
        Solicitation.target_id == target_id,
    )
    return query.first()

def delete_all_solicitation_by_source(source_id):
    query = db.session.query(
        Solicitation
    ).filter(
        Solicitation.source_id == source_id,
    )
    query.delete()

def has_recent_solicitations(source_id):
    query = db.session.query(
        Solicitation
    ).filter(
        Solicitation.source_id == source_id,
        Solicitation.created > datetime.utcnow() - timedelta(hours=24),
    )
    return query.count() > 0

def find_latest_solicitation_by_source(source_id):
    query = db.session.query(
        Solicitation
    ).filter(
        Solicitation.source_id == source_id,
    )
    return query.order_by(Solicitation.created.desc()).first()

def has_too_many_actions_per_min(source_domain):
    query = Report.query.filter_by(
        source_domain=source_domain
    ).filter(
        Report.created > datetime.utcnow() - timedelta(minutes=1),
    )
    return query.count() > 20

def get_instance_flag(instance_id, flag_enum):
    query = InstanceFlag.query.filter(
        InstanceFlag.instance_id == instance_id,
        InstanceFlag.flag == flag_enum,
    )
    return query.first()

def instance_has_flag(instance_id, flag_enum):
    query = InstanceFlag.query.filter(
        InstanceFlag.instance_id == instance_id,
        InstanceFlag.flag == flag_enum,
    )
    return query.count() == 1

def get_instance_tag(instance_id, tag: str):
    query = InstanceTag.query.filter(
        InstanceTag.instance_id == instance_id,
        InstanceTag.tag == tag,
    )
    return query.first()

def instance_has_tag(instance_id, tag: str):
    query = InstanceTag.query.filter(
        InstanceTag.instance_id == instance_id,
        InstanceTag.tag == tag.lower(),
    )
    return query.count() == 1

def count_instance_tags(instance_id):
    query = InstanceTag.query.filter(
        InstanceTag.instance_id == instance_id,
    )
    return query.count()

def get_tag_counts():
    query = db.session.query(
        func.lower(InstanceTag.tag).label('tag'),
        func.count().label('tag_count')
    ).group_by(InstanceTag.tag)

    result = query.all()

    tag_counts = {row.tag: row.tag_count for row in result}
    return tag_counts