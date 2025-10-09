"""
XML Generation Service
Generates ICH E2B R3 XML files from ICSR data
"""

import asyncio
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
import structlog
from datetime import datetime
import uuid

from models.simple_icsr_models import ICSRData, XMLGenerationResponse

logger = structlog.get_logger()

class XMLGenerationService:
    def __init__(self):
        self.ich_e2b_namespace = "http://www.ich.org/fileadmin/Public_Web_Site/ICH_Products/Guidelines/Efficacy/E2B/E2B_R3/ICH_E2B_R3.xsd"
        self.xml_template = {
            'ichicsr': {
                'xmlns': self.ich_e2b_namespace,
                'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                'xsi:schemaLocation': f'{self.ich_e2b_namespace} ICH_E2B_R3.xsd'
            }
        }
    
    async def generate_ich_e2b_xml(
        self,
        icsr_data: ICSRData,
        format_version: str = "R3",
        include_attachments: bool = True
    ) -> XMLGenerationResponse:
        """
        Generate ICH E2B R3 XML file from ICSR data
        """
        logger.info("Starting XML generation", icsr_id=icsr_data.icsr_id, format_version=format_version)
        
        try:
            # Create root element
            root = ET.Element('ichicsr')
            root.set('xmlns', self.ich_e2b_namespace)
            root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
            root.set('xsi:schemaLocation', f'{self.ich_e2b_namespace} ICH_E2B_R3.xsd')
            
            # Add message header
            message_header = self._create_message_header(icsr_data)
            root.append(message_header)
            
            # Add safety report
            safety_report = self._create_safety_report(icsr_data)
            root.append(safety_report)
            
            # Add attachments if requested
            if include_attachments and icsr_data.additional_information:
                attachments = self._create_attachments(icsr_data)
                if attachments:
                    root.append(attachments)
            
            # Generate XML string
            xml_content = self._format_xml(root)
            
            # Validate XML
            validation_status = await self._validate_xml(xml_content)
            
            # Generate filename
            file_name = f"ICSR_{icsr_data.icsr_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
            
            logger.info("XML generation completed", 
                       icsr_id=icsr_data.icsr_id,
                       xml_size=len(xml_content),
                       validation_status=validation_status)
            
            return XMLGenerationResponse(
                success=True,
                xml_content=xml_content,
                file_name=file_name,
                validation_status=validation_status
            )
            
        except Exception as e:
            logger.error("XML generation failed", error=str(e))
            return XMLGenerationResponse(
                success=False,
                xml_content="",
                file_name="",
                validation_status="invalid"
            )
    
    def _create_message_header(self, icsr_data: ICSRData) -> ET.Element:
        """Create message header section"""
        message_header = ET.Element('messageheader')
        
        # Message details
        messagenum = ET.SubElement(message_header, 'messagenum')
        messagenum.text = icsr_data.icsr_id
        
        messagesenderidentifier = ET.SubElement(message_header, 'messagesenderidentifier')
        messagesenderidentifier.text = "LiteratureAutomation"
        
        messagereceiveridentifier = ET.SubElement(message_header, 'messagereceiveridentifier')
        messagereceiveridentifier.text = "RegulatoryAuthority"
        
        messagedateformat = ET.SubElement(message_header, 'messagedateformat')
        messagedateformat.text = "204"  # CCYYMMDDHHMM
        
        messagedate = ET.SubElement(message_header, 'messagedate')
        messagedate.text = datetime.now().strftime('%Y%m%d%H%M')
        
        return message_header
    
    def _create_safety_report(self, icsr_data: ICSRData) -> ET.Element:
        """Create safety report section"""
        safety_report = ET.Element('safetyreport')
        
        # Safety report identification
        safetyreportversion = ET.SubElement(safety_report, 'safetyreportversion')
        safetyreportversion.text = "1"
        
        safetyreportid = ET.SubElement(safety_report, 'safetyreportid')
        safetyreportid.text = icsr_data.icsr_id
        
        primarysourcecountry = ET.SubElement(safety_report, 'primarysourcecountry')
        primarysourcecountry.text = icsr_data.general_information.country
        
        occurrencecountry = ET.SubElement(safety_report, 'occurrencecountry')
        occurrencecountry.text = icsr_data.general_information.country
        
        # Report type
        reporttype = ET.SubElement(safety_report, 'reporttype')
        reporttype.text = "1"  # Spontaneous
        
        # Seriousness
        seriousness = ET.SubElement(safety_report, 'seriousness')
        if icsr_data.event_information.seriousness_criteria:
            seriousness.text = "1"  # Serious
        else:
            seriousness.text = "2"  # Non-serious
        
        # Add patient information
        patient = self._create_patient_section(icsr_data)
        safety_report.append(patient)
        
        # Add reaction information
        reaction = self._create_reaction_section(icsr_data)
        safety_report.append(reaction)
        
        # Add drug information
        drug = self._create_drug_section(icsr_data)
        safety_report.append(drug)
        
        return safety_report
    
    def _create_patient_section(self, icsr_data: ICSRData) -> ET.Element:
        """Create patient section"""
        patient = ET.Element('patient')
        
        # Patient details
        if icsr_data.patient_information.patient_details:
            patient_details = icsr_data.patient_information.patient_details
            
            # Patient age
            if patient_details.get('age'):
                patientonsetage = ET.SubElement(patient, 'patientonsetage')
                patientonsetage.text = str(patient_details['age'])
                
                patientonsetageunit = ET.SubElement(patient, 'patientonsetageunit')
                age_unit = patient_details.get('age_unit', '801')  # Years
                unit_mapping = {
                    'Days': '802',
                    'Weeks': '803',
                    'Months': '804',
                    'Years': '801'
                }
                patientonsetageunit.text = unit_mapping.get(age_unit, '801')
            
            # Patient sex
            if patient_details.get('gender'):
                patientsex = ET.SubElement(patient, 'patientsex')
                gender_mapping = {
                    'Male': '1',
                    'Female': '2',
                    'Unknown': '0'
                }
                patientsex.text = gender_mapping.get(patient_details['gender'], '0')
        
        return patient
    
    def _create_reaction_section(self, icsr_data: ICSRData) -> ET.Element:
        """Create reaction section"""
        reaction = ET.Element('reaction')
        
        # Reaction term
        if icsr_data.event_information.description_as_reported:
            reactionmeddrapt = ET.SubElement(reaction, 'reactionmeddrapt')
            reactionmeddrapt.text = icsr_data.event_information.description_as_reported
        
        # Reaction outcome
        if icsr_data.event_information.outcome:
            reactionoutcome = ET.SubElement(reaction, 'reactionoutcome')
            outcome_mapping = {
                'Fatal': '1',
                'Recovering': '2',
                'Not Recovered': '3',
                'Recovered': '4',
                'Recovered with Sequelae': '5',
                'Unknown': '6'
            }
            reactionoutcome.text = outcome_mapping.get(icsr_data.event_information.outcome, '6')
        
        return reaction
    
    def _create_drug_section(self, icsr_data: ICSRData) -> ET.Element:
        """Create drug section"""
        drug = ET.Element('drug')
        
        # Drug characterization
        drugcharacterization = ET.SubElement(drug, 'drugcharacterization')
        drugcharacterization.text = "1"  # Suspect
        
        # Medicinal product name
        if icsr_data.product_information.suspect_products:
            first_product = icsr_data.product_information.suspect_products[0]
            if first_product.get('generic_name'):
                medicinalproduct = ET.SubElement(drug, 'medicinalproduct')
                medicinalproduct.text = first_product['generic_name']
        
        return drug
    
    def _create_attachments(self, icsr_data: ICSRData) -> ET.Element:
        """Create attachments section"""
        attachments = ET.Element('attachments')
        
        if icsr_data.additional_information and icsr_data.additional_information.source_document_attachments:
            for i, attachment in enumerate(icsr_data.additional_information.source_document_attachments):
                attachment_elem = ET.SubElement(attachments, 'attachment')
                
                attachmentid = ET.SubElement(attachment_elem, 'attachmentid')
                attachmentid.text = f"ATT_{i+1}"
                
                attachmentfilename = ET.SubElement(attachment_elem, 'attachmentfilename')
                attachmentfilename.text = attachment
        
        return attachments
    
    def _format_xml(self, root: ET.Element) -> str:
        """Format XML with proper indentation"""
        # Convert to string
        xml_str = ET.tostring(root, encoding='unicode')
        
        # Add XML declaration
        xml_content = f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'
        
        return xml_content
    
    async def _validate_xml(self, xml_content: str) -> str:
        """Validate generated XML"""
        try:
            # Basic XML validation
            ET.fromstring(xml_content)
            return "valid"
        except ET.ParseError as e:
            logger.error("XML validation failed", error=str(e))
            return "invalid"
        except Exception as e:
            logger.error("XML validation error", error=str(e))
            return "invalid"
