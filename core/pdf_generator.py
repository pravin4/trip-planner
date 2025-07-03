import os
from datetime import datetime
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from models.travel_models import Itinerary, DayPlan, Activity, Restaurant
import logging

logger = logging.getLogger(__name__)


class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the itinerary"""
        
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Section header style
        self.section_style = ParagraphStyle(
            'CustomSection',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        )
        
        # Subsection style
        self.subsection_style = ParagraphStyle(
            'CustomSubsection',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.darkgreen
        )
        
        # Normal text style
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6
        )
        
        # Highlighted text style
        self.highlight_style = ParagraphStyle(
            'CustomHighlight',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            textColor=colors.darkred,
            fontName='Helvetica-Bold'
        )
    
    def generate_itinerary_pdf(self, itinerary: Dict[str, Any], output_path: str) -> bool:
        """Generate a complete PDF itinerary"""
        try:
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            story = []
            
            # Add title page
            story.extend(self._create_title_page(itinerary))
            story.append(PageBreak())
            
            # Add trip overview
            story.extend(self._create_trip_overview(itinerary))
            story.append(PageBreak())
            
            # Add day-by-day itinerary
            story.extend(self._create_daily_itinerary(itinerary))
            
            # Add cost breakdown
            story.append(PageBreak())
            story.extend(self._create_cost_breakdown(itinerary))
            
            # Add travel tips
            story.append(PageBreak())
            story.extend(self._create_travel_tips(itinerary))
            
            # Build the PDF
            doc.build(story)
            
            logger.info(f"PDF itinerary generated successfully: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            return False
    
    def _create_title_page(self, itinerary: Dict[str, Any]) -> List[Any]:
        """Create the title page"""
        story = []
        
        # Main title
        title = f"Travel Itinerary: {itinerary['destination']}"
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 20))
        
        # Trip dates
        start_date = datetime.strptime(itinerary['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(itinerary['end_date'], '%Y-%m-%d')
        date_range = f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}"
        story.append(Paragraph(date_range, self.section_style))
        story.append(Spacer(1, 30))
        
        # Trip summary
        duration_days = len(itinerary['day_plans'])
        summary_data = [
            ["Destination:", itinerary['destination']],
            ["Duration:", f"{duration_days} days"],
            ["Total Budget:", f"${itinerary['total_budget']:,.2f}"],
            ["Estimated Cost:", f"${itinerary['total_cost']:,.2f}"],
            ["Budget Status:", "✅ Within Budget" if itinerary['total_cost'] <= itinerary['total_budget'] else "⚠️ Over Budget"]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 30))
        
        # Generated timestamp
        timestamp = f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        story.append(Paragraph(timestamp, self.normal_style))
        
        return story
    
    def _create_trip_overview(self, itinerary: Dict[str, Any]) -> List[Any]:
        """Create trip overview section"""
        story = []
        
        story.append(Paragraph("Trip Overview", self.section_style))
        story.append(Spacer(1, 12))
        
        # Preferences summary
        story.append(Paragraph("Travel Preferences", self.subsection_style))
        
        prefs = itinerary['preferences']
        prefs_data = [
            ["Accommodation Types:", ", ".join([t.title() for t in prefs.get('accommodation_types', [])])],
            ["Activity Types:", ", ".join([t.title() for t in prefs.get('activity_types', [])])],
            ["Budget Level:", prefs.get('budget_level', 'moderate').title()],
            ["Group Size:", str(prefs.get('group_size', 1))],
            ["Children:", "Yes" if prefs.get('children', False) else "No"],
            ["Dietary Restrictions:", ", ".join(prefs.get('dietary_restrictions', [])) if prefs.get('dietary_restrictions') else "None"]
        ]
        
        prefs_table = Table(prefs_data, colWidths=[2*inch, 3*inch])
        prefs_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(prefs_table)
        story.append(Spacer(1, 20))
        
        # Destination highlights
        story.append(Paragraph("Destination Highlights", self.subsection_style))
        
        # Count activities by type
        activity_counts = {}
        for day_plan in itinerary['day_plans']:
            for activity in day_plan.get('activities', []):
                if isinstance(activity, dict):
                    activity_type = activity.get('type', 'unknown')
                else:
                    activity_type = activity.type.value
                activity_counts[activity_type] = activity_counts.get(activity_type, 0) + 1
        
        if activity_counts:
            highlights_data = [["Activity Type", "Count"]]
            for activity_type, count in activity_counts.items():
                highlights_data.append([activity_type.title(), str(count)])
            
            highlights_table = Table(highlights_data, colWidths=[2*inch, 1*inch])
            highlights_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(highlights_table)
        
        return story
    
    def _create_daily_itinerary(self, itinerary: Dict[str, Any]) -> List[Any]:
        """Create day-by-day itinerary section"""
        story = []
        
        story.append(Paragraph("Daily Itinerary", self.section_style))
        story.append(Spacer(1, 12))
        
        for i, day_plan in enumerate(itinerary['day_plans'], 1):
            story.extend(self._create_single_day_plan(day_plan, i))
            
            # Add page break between days if not the last day
            if i < len(itinerary['day_plans']):
                story.append(PageBreak())
        
        return story
    
    def _create_single_day_plan(self, day_plan: Dict[str, Any], day_number: int) -> List[Any]:
        """Create a single day's plan"""
        story = []
        
        # Day header
        day_date = datetime.strptime(day_plan['date'], '%Y-%m-%d')
        day_title = f"Day {day_number}: {day_date.strftime('%A, %B %d, %Y')}"
        story.append(Paragraph(day_title, self.subsection_style))
        story.append(Spacer(1, 8))
        
        # Activities
        if day_plan.get('activities'):
            story.append(Paragraph("Activities", self.normal_style))
            
            activities_data = [["Time", "Activity", "Duration", "Cost"]]
            current_time = 9  # Start at 9 AM
            
            for activity in day_plan['activities']:
                time_slot = f"{current_time}:00 AM"
                if isinstance(activity, dict):
                    activities_data.append([
                        time_slot,
                        activity.get('name', 'Unknown'),
                        f"{activity.get('duration_hours', 1)}h",
                        f"${activity.get('cost', 0):.2f}"
                    ])
                    current_time += int(activity.get('duration_hours', 1)) + 1
                else:
                    activities_data.append([
                        time_slot,
                        activity.name,
                        f"{activity.duration_hours}h",
                        f"${activity.cost:.2f}"
                    ])
                    current_time += int(activity.duration_hours) + 1
            
            activities_table = Table(activities_data, colWidths=[1*inch, 2.5*inch, 0.8*inch, 0.7*inch])
            activities_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            
            story.append(activities_table)
            story.append(Spacer(1, 12))
        
        # Restaurants
        if day_plan.get('restaurants'):
            story.append(Paragraph("Dining", self.normal_style))
            
            restaurants_data = [["Restaurant", "Cuisine", "Price Level", "Cost/Person"]]
            for restaurant in day_plan['restaurants']:
                if isinstance(restaurant, dict):
                    price_level = "$" * restaurant.get('price_level', 2)
                    restaurants_data.append([
                        restaurant.get('name', 'Unknown'),
                        restaurant.get('cuisine_type', 'Local'),
                        price_level,
                        f"${restaurant.get('cost_per_person', 30):.2f}"
                    ])
                else:
                    price_level = "$" * restaurant.price_level
                    restaurants_data.append([
                        restaurant.name,
                        restaurant.cuisine_type,
                        price_level,
                        f"${restaurant.cost_per_person:.2f}"
                    ])
            
            restaurants_table = Table(restaurants_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1*inch])
            restaurants_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkorange),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            
            story.append(restaurants_table)
            story.append(Spacer(1, 12))
        
        # Transportation
        if day_plan.get('transportation') or day_plan.get('local_transportation'):
            story.append(Paragraph("Transportation", self.normal_style))
            
            # Inter-city transportation
            if day_plan.get('transportation_cost', 0) > 0:
                story.append(Paragraph(f"Inter-city travel: ${day_plan.get('transportation_cost', 0):.2f}", self.normal_style))
            
            # Local transportation
            if day_plan.get('local_transportation'):
                local_transport_data = [["From", "To", "Mode", "Duration", "Cost"]]
                for transport in day_plan['local_transportation']:
                    local_transport_data.append([
                        transport.get('from', 'Unknown'),
                        transport.get('to', 'Unknown'),
                        transport.get('mode', 'Unknown').title(),
                        f"{transport.get('duration_minutes', 0)} min",
                        f"${transport.get('cost_per_person', 0):.2f}"
                    ])
                
                local_transport_table = Table(local_transport_data, colWidths=[1.2*inch, 1.2*inch, 0.8*inch, 0.8*inch, 0.8*inch])
                local_transport_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey)
                ]))
                
                story.append(local_transport_table)
            
            # Legacy transportation info
            elif day_plan.get('transportation'):
                for transport in day_plan['transportation']:
                    story.append(Paragraph(f"• {transport}", self.normal_style))
            
            story.append(Spacer(1, 12))
        
        # Notes
        if day_plan.get('notes'):
            story.append(Paragraph("Notes", self.normal_style))
            story.append(Paragraph(day_plan['notes'], self.normal_style))
        
        return story
    
    def _create_cost_breakdown(self, itinerary: Dict[str, Any]) -> List[Any]:
        """Create cost breakdown section"""
        story = []
        
        story.append(Paragraph("Cost Breakdown", self.section_style))
        story.append(Spacer(1, 12))
        
        # Cost breakdown table
        cost_breakdown = itinerary['cost_breakdown']
        total_cost = itinerary['total_cost']
        cost_data = [
            ["Category", "Amount", "Percentage"],
            ["Accommodation", f"${cost_breakdown.get('accommodations', 0):,.2f}", 
             f"{(cost_breakdown.get('accommodations', 0) / total_cost * 100):.1f}%"],
            ["Activities", f"${cost_breakdown.get('activities', 0):,.2f}",
             f"{(cost_breakdown.get('activities', 0) / total_cost * 100):.1f}%"],
            ["Restaurants", f"${cost_breakdown.get('restaurants', 0):,.2f}",
             f"{(cost_breakdown.get('restaurants', 0) / total_cost * 100):.1f}%"],
            ["Transportation", f"${cost_breakdown.get('transportation', 0):,.2f}",
             f"{(cost_breakdown.get('transportation', 0) / total_cost * 100):.1f}%"],
            ["Miscellaneous", f"${cost_breakdown.get('miscellaneous', 0):,.2f}",
             f"{(cost_breakdown.get('miscellaneous', 0) / total_cost * 100):.1f}%"],
            ["", "", ""],
            ["TOTAL", f"${total_cost:,.2f}", "100%"]
        ]
        
        cost_table = Table(cost_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
        cost_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('BACKGROUND', (0, -2), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('TEXTCOLOR', (0, 1), (-1, -3), colors.black),
            ('TEXTCOLOR', (0, -2), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold')
        ]))
        
        story.append(cost_table)
        story.append(Spacer(1, 20))
        
        # Budget summary
        total_budget = itinerary['total_budget']
        remaining_budget = total_budget - total_cost
        budget_status = "✅ Within Budget" if remaining_budget >= 0 else "⚠️ Over Budget"
        budget_text = f"Budget: ${total_budget:,.2f} | Estimated Cost: ${total_cost:,.2f} | Status: {budget_status}"
        story.append(Paragraph(budget_text, self.highlight_style))
        
        if remaining_budget < 0:
            overspend_text = f"Over budget by: ${abs(remaining_budget):,.2f}"
            story.append(Paragraph(overspend_text, self.highlight_style))
        else:
            remaining_text = f"Remaining budget: ${remaining_budget:,.2f}"
            story.append(Paragraph(remaining_text, self.normal_style))
        
        return story
    
    def _create_travel_tips(self, itinerary: Dict[str, Any]) -> List[Any]:
        """Create travel tips section"""
        story = []
        
        story.append(Paragraph("Travel Tips & Recommendations", self.section_style))
        story.append(Spacer(1, 12))
        
        tips = [
            "📱 Download offline maps for your destination",
            "💳 Carry multiple payment methods (cash and cards)",
            "📞 Save important local numbers (hotel, emergency services)",
            "🌤️ Check weather forecasts before your trip",
            "🎫 Book popular attractions in advance when possible",
            "🚇 Research public transportation options",
            "🍽️ Make restaurant reservations for popular dining spots",
            "📸 Keep copies of important documents (passport, tickets)",
            "💊 Pack any necessary medications",
            "🔌 Bring appropriate power adapters for your destination"
        ]
        
        for tip in tips:
            story.append(Paragraph(tip, self.normal_style))
        
        story.append(Spacer(1, 20))
        
        # Emergency information
        story.append(Paragraph("Emergency Information", self.subsection_style))
        emergency_info = [
            "Emergency Services: 911 (US) / 112 (EU)",
            "Local Police: Check with your hotel for local numbers",
            "Medical Emergency: Contact your hotel concierge",
            "Lost Passport: Contact your embassy immediately"
        ]
        
        for info in emergency_info:
            story.append(Paragraph(info, self.normal_style))
        
        return story 