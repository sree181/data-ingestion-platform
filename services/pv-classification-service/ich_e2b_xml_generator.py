"""
ICH E2B R3 XML Generator
Generates regulatory-compliant ICH E2B R3 XML files for ICSR data
"""
import uuid
import structlog
from datetime import datetime
from typing import Optional
from lxml import etree
from icsr_extractor import ICSRData

logger = structlog.get_logger(__name__)


class ICHE2BR3XMLGenerator:
    """
    Generates ICH E2B R3 XML format for ICSR submissions
    Compliant with FDA, EMA, and ICH standards
    """
    
    def __init__(self):
        self.namespace = "http://www.ich.org/ICSR/2.1"
        self.ns_map = {
            None: self.namespace,
            'xsi': "http://www.w3.org/2001/XMLSchema-instance"
        }
        logger.info("ICH E2B R3 XML Generator initialized")
    
    def generate_xml(
        self,
        icsr_data: ICSRData,
        sender_id: str = "MAH001",
        receiver_id: str = "FDA",
        message_type: str = "ichicsr",
        message_format_version: str = "2.1"
    ) -> str:
        """
        Generate ICH E2B R3 XML from ICSR data
        
        Args:
            icsr_data: Extracted ICSR data
            sender_id: Sender organization ID
            receiver_id: Receiver organization ID (FDA, EMA, etc.)
            message_type: Message type (ichicsr)
            message_format_version: ICH E2B version
            
        Returns:
            XML string
        """
        try:
            logger.info("Generating ICH E2B R3 XML")
            
            # Create root element
            root = etree.Element(
                "ichicsr",
                nsmap=self.ns_map,
                attrib={
                    "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation": 
                    "http://www.ich.org/ICSR/2.1 ICSR21.xsd"
                }
            )
            
            # Add message header
            self._add_message_header(
                root, sender_id, receiver_id,
                message_type, message_format_version
            )
            
            # Add safety report
            self._add_safety_report(root, icsr_data)
            
            # Convert to string
            xml_string = etree.tostring(
                root,
                pretty_print=True,
                xml_declaration=True,
                encoding='UTF-8'
            ).decode('utf-8')
            
            logger.info("ICH E2B R3 XML generated successfully")
            
            return xml_string
            
        except Exception as e:
            logger.error("XML generation failed", error=str(e), exc_info=True)
            raise
    
    def _add_message_header(
        self,
        root: etree.Element,
        sender_id: str,
        receiver_id: str,
        message_type: str,
        message_format_version: str
    ):
        """Add ICH message header"""
        
        # Generate unique message ID
        message_id = f"MSG-{uuid.uuid4()}"
        message_date = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        
        # ichicsrmessageheader
        header = etree.SubElement(root, "ichicsrmessageheader")
        
        etree.SubElement(header, "messagetype").text = message_type
        etree.SubElement(header, "messageformatversion").text = message_format_version
        etree.SubElement(header, "messageformatrelease").text = "2.1"
        etree.SubElement(header, "messagenumb").text = message_id
        etree.SubElement(header, "messagesenderidentifier").text = sender_id
        etree.SubElement(header, "messagereceiveridentifier").text = receiver_id
        etree.SubElement(header, "messagedateformat").text = "204"
        etree.SubElement(header, "messagedate").text = message_date
    
    def _add_safety_report(self, root: etree.Element, icsr_data: ICSRData):
        """Add safety report section"""
        
        # safetyreport
        safety_report = etree.SubElement(root, "safetyreport")
        
        # Generate safety report ID
        safety_report_id = f"ICSR-{uuid.uuid4()}"
        etree.SubElement(safety_report, "safetyreportid").text = safety_report_id
        
        # Primary source
        self._add_primary_source(safety_report, icsr_data)
        
        # Sender
        self._add_sender(safety_report)
        
        # Receiver
        self._add_receiver(safety_report)
        
        # Patient
        self._add_patient(safety_report, icsr_data)
    
    def _add_primary_source(self, parent: etree.Element, icsr_data: ICSRData):
        """Add primary source (reporter) information"""
        
        primary_source = etree.SubElement(parent, "primarysource")
        
        if icsr_data.reporter:
            reporter = icsr_data.reporter
            
            # Reporter name
            if reporter.first_name or reporter.last_name:
                name = f"{reporter.first_name or ''} {reporter.last_name or ''}".strip()
                etree.SubElement(primary_source, "reportergivename").text = reporter.first_name or ""
                etree.SubElement(primary_source, "reporterfamilyname").text = reporter.last_name or ""
            
            # Reporter qualification (1=Physician, 2=Pharmacist, 3=Other HCP, 4=Lawyer, 5=Consumer)
            if reporter.is_hcp:
                if reporter.occupation and "physician" in reporter.occupation.lower():
                    etree.SubElement(primary_source, "qualification").text = "1"
                elif reporter.occupation and "pharmacist" in reporter.occupation.lower():
                    etree.SubElement(primary_source, "qualification").text = "2"
                else:
                    etree.SubElement(primary_source, "qualification").text = "3"
            else:
                etree.SubElement(primary_source, "qualification").text = "5"
        
        # Literature reference
        if icsr_data.literature:
            lit = icsr_data.literature
            literature_ref = etree.SubElement(primary_source, "literaturereference")
            
            if lit.author:
                etree.SubElement(literature_ref, "reportergivename").text = lit.author
            if lit.title:
                etree.SubElement(literature_ref, "reporterfamilyname").text = lit.title[:100]
    
    def _add_sender(self, parent: etree.Element):
        """Add sender information"""
        
        sender = etree.SubElement(parent, "sender")
        etree.SubElement(sender, "sendertype").text = "2"  # 2 = Marketing Authorization Holder
        etree.SubElement(sender, "senderorganization").text = "Marketing Authorization Holder"
    
    def _add_receiver(self, parent: etree.Element):
        """Add receiver information"""
        
        receiver = etree.SubElement(parent, "receiver")
        etree.SubElement(receiver, "receivertype").text = "1"  # 1 = Regulatory Authority
        etree.SubElement(receiver, "receiverorganization").text = "FDA"
    
    def _add_patient(self, parent: etree.Element, icsr_data: ICSRData):
        """Add patient information"""
        
        patient_elem = etree.SubElement(parent, "patient")
        
        if icsr_data.patient:
            p = icsr_data.patient
            
            # Patient characteristics
            if p.initials:
                etree.SubElement(patient_elem, "patientinitial").text = p.initials
            
            # Age
            if p.age:
                etree.SubElement(patient_elem, "patientonsetage").text = str(p.age)
                # Age unit (800=Decade, 801=Year, 802=Month, 803=Week, 804=Day, 805=Hour)
                age_unit_map = {
                    "Years": "801",
                    "Months": "802",
                    "Weeks": "803",
                    "Days": "804",
                    "Decades": "800"
                }
                etree.SubElement(patient_elem, "patientonsetageunit").text = age_unit_map.get(p.age_unit, "801")
            
            # Gender (1=Male, 2=Female, 0=Unknown)
            if p.gender:
                gender_map = {"Male": "1", "Female": "2", "Unknown": "0"}
                etree.SubElement(patient_elem, "patientsex").text = gender_map.get(p.gender, "0")
            
            # Weight
            if p.weight_kg:
                etree.SubElement(patient_elem, "patientweight").text = str(p.weight_kg)
            
            # Medical history
            if p.medical_history:
                medical_history = etree.SubElement(patient_elem, "medicalhistoryepisode")
                etree.SubElement(medical_history, "patientepisodename").text = p.medical_history[:250]
        
        # Death information
        if icsr_data.death_details and icsr_data.death_details.cause_of_death:
            death = etree.SubElement(patient_elem, "patientdeath")
            etree.SubElement(death, "patientdeathdateformat").text = "102"
            if icsr_data.death_details.date_of_death:
                etree.SubElement(death, "patientdeathdate").text = icsr_data.death_details.date_of_death.replace("-", "")
        
        # Drugs
        self._add_drugs(patient_elem, icsr_data)
        
        # Reactions
        self._add_reactions(patient_elem, icsr_data)
        
        # Summary/Narrative
        if icsr_data.case_narrative:
            summary = etree.SubElement(patient_elem, "summary")
            etree.SubElement(summary, "narrativeincludeclinical").text = icsr_data.case_narrative[:10000]
    
    def _add_drugs(self, parent: etree.Element, icsr_data: ICSRData):
        """Add drug information"""
        
        # Suspect products
        for idx, product in enumerate(icsr_data.suspect_products, 1):
            drug = etree.SubElement(parent, "drug")
            
            etree.SubElement(drug, "drugcharacterization").text = "1"  # 1 = Suspect
            
            if product.generic_name:
                etree.SubElement(drug, "medicinalproduct").text = product.generic_name
            elif product.brand_name:
                etree.SubElement(drug, "medicinalproduct").text = product.brand_name
            
            # Indication
            if product.indication:
                indication = etree.SubElement(drug, "drugindication")
                etree.SubElement(indication, "drugindication").text = product.indication
            
            # Dosage
            if product.dose:
                dosage = etree.SubElement(drug, "drugdosagetext")
                dosage.text = f"{product.dose} {product.route or ''} {product.frequency or ''}".strip()
            
            # Route (001=Auricular, 002=Buccal, 003=Cutaneous, etc.)
            if product.route:
                route_map = {
                    "Oral": "048",
                    "IV": "042",
                    "IM": "032",
                    "Subcutaneous": "058",
                    "Topical": "065"
                }
                route_code = route_map.get(product.route, "048")
                etree.SubElement(drug, "drugadministrationroute").text = route_code
            
            # Action taken (1=Drug withdrawn, 2=Dose reduced, 3=Dose increased, 4=Dose not changed, 5=Unknown, 6=Not applicable)
            if product.action_taken:
                action_map = {
                    "Permanently Discontinued": "1",
                    "Temporary Withdrawal": "1",
                    "Dose Decreased": "2",
                    "Dose Increased": "3",
                    "Dose Not Changed": "4",
                    "Unknown": "5",
                    "Not Applicable": "6"
                }
                etree.SubElement(drug, "actiondrug").text = action_map.get(product.action_taken, "5")
        
        # Concomitant products
        for product in icsr_data.concomitant_products:
            drug = etree.SubElement(parent, "drug")
            
            etree.SubElement(drug, "drugcharacterization").text = "2"  # 2 = Concomitant
            
            if product.generic_name:
                etree.SubElement(drug, "medicinalproduct").text = product.generic_name
            elif product.brand_name:
                etree.SubElement(drug, "medicinalproduct").text = product.brand_name
    
    def _add_reactions(self, parent: etree.Element, icsr_data: ICSRData):
        """Add reaction/event information"""
        
        for event in icsr_data.events:
            reaction = etree.SubElement(parent, "reaction")
            
            # MedDRA term
            if event.meddra_pt:
                etree.SubElement(reaction, "reactionmeddrapt").text = event.meddra_pt
            else:
                # Use description if MedDRA not available
                etree.SubElement(reaction, "reactionmeddrapt").text = event.description[:100]
            
            # Seriousness (1=Yes, 2=No)
            if event.seriousness_criteria:
                etree.SubElement(reaction, "reactionserious").text = "1"
                
                # Seriousness criteria
                if "Death" in event.seriousness_criteria:
                    etree.SubElement(reaction, "reactionseriousnessdeath").text = "1"
                if "Life-threatening" in event.seriousness_criteria:
                    etree.SubElement(reaction, "reactionseriousnesslifethreatening").text = "1"
                if "Hospitalization" in event.seriousness_criteria or "Prolonged hospitalization" in event.seriousness_criteria:
                    etree.SubElement(reaction, "reactionseriousnesshospitalization").text = "1"
                if "Disability" in event.seriousness_criteria:
                    etree.SubElement(reaction, "reactionseriousnessdisabling").text = "1"
                if "Congenital Anomaly" in event.seriousness_criteria:
                    etree.SubElement(reaction, "reactionseriousnesscongenitalanomali").text = "1"
                if "Medically Significant" in event.seriousness_criteria:
                    etree.SubElement(reaction, "reactionseriousnessother").text = "1"
            else:
                etree.SubElement(reaction, "reactionserious").text = "2"
            
            # Outcome (1=Recovered, 2=Recovering, 3=Not recovered, 4=Recovered with sequelae, 5=Fatal, 6=Unknown)
            if event.outcome:
                outcome_map = {
                    "Recovered": "1",
                    "Recovering": "2",
                    "Not Recovered": "3",
                    "Recovered with Sequelae": "4",
                    "Fatal": "5",
                    "Unknown": "6"
                }
                etree.SubElement(reaction, "reactionoutcome").text = outcome_map.get(event.outcome, "6")


# Initialize service
xml_generator = ICHE2BR3XMLGenerator()
