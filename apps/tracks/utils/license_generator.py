# apps/tracks/utils/license_generator.py

import os
from datetime import datetime
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def generate_license_certificate(purchase):
    """Generate a PDF license certificate for a purchase"""

    buffer = BytesIO()

    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )

    # Container for the 'Flowable' objects
    story = []

    # Get styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#2c3e50'),
        alignment=1  # Center alignment
    )

    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor('#34495e'),
        alignment=0  # Left alignment
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        textColor=colors.HexColor('#2c3e50'),
        alignment=0
    )

    # Title
    story.append(Paragraph("MUSIC LICENSE CERTIFICATE", title_style))
    story.append(Spacer(1, 20))

    # Certificate info
    cert_info = f"""
    <b>Certificate ID:</b> {purchase.public_id}<br/>
    <b>Issue Date:</b> {purchase.purchased_at.strftime('%B %d, %Y')}<br/>
    <b>License Type:</b> {purchase.license_type.display_name}
    """
    story.append(Paragraph(cert_info, body_style))
    story.append(Spacer(1, 20))

    # Track Information
    story.append(Paragraph("TRACK INFORMATION", header_style))

    track_data = [
        ['Track Title:', purchase.track.title],
        ['Artist:',
         f"{purchase.track.artist.first_name} {purchase.track.artist.last_name} (@{purchase.track.artist.username})"],
        ['Genre:', purchase.track.genre.name if purchase.track.genre else 'Not specified'],
        ['Duration:', purchase.track.duration_formatted],
        ['BPM:', str(purchase.track.bpm) if purchase.track.bpm else 'Not specified'],
        ['Key:', purchase.track.key or 'Not specified'],
    ]

    track_table = Table(track_data, colWidths=[2 * inch, 4 * inch])
    track_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(track_table)
    story.append(Spacer(1, 20))

    # License Holder Information
    story.append(Paragraph("LICENSE HOLDER", header_style))

    buyer_data = [
        ['Name:', f"{purchase.buyer.first_name} {purchase.buyer.last_name}"],
        ['Username:', f"@{purchase.buyer.username}"],
        ['Email:', purchase.buyer.email],
        ['Purchase Date:', purchase.purchased_at.strftime('%B %d, %Y at %I:%M %p')],
        ['Amount Paid:', f"${purchase.price_paid} {purchase.currency}"],
    ]

    buyer_table = Table(buyer_data, colWidths=[2 * inch, 4 * inch])
    buyer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(buyer_table)
    story.append(Spacer(1, 20))

    # License Terms
    story.append(Paragraph("LICENSE TERMS & PERMISSIONS", header_style))

    license_terms = f"""
    <b>License Description:</b><br/>
    {purchase.license_type.description}
    <br/><br/>
    <b>Permissions Granted:</b><br/>
    • Commercial Use: {'✓ Allowed' if purchase.license_type.allows_commercial_use else '✗ Not Allowed'}<br/>
    • Modification: {'✓ Allowed' if purchase.license_type.allows_modification else '✗ Not Allowed'}<br/>
    • Attribution Required: {'✓ Yes' if purchase.license_type.requires_attribution else '✗ No'}<br/>
    • Maximum Copies: {purchase.license_type.max_copies if purchase.license_type.max_copies else 'Unlimited'}
    <br/><br/>
    <b>Download Information:</b><br/>
    • Downloads Used: {purchase.download_count} of {purchase.max_downloads}<br/>
    • Downloads Remaining: {purchase.max_downloads - purchase.download_count}
    """

    story.append(Paragraph(license_terms, body_style))
    story.append(Spacer(1, 30))

    # Footer
    footer_text = f"""
    <br/><br/>
    This certificate confirms that the above-named license holder has legally 
    purchased the rights to use the specified track according to the terms outlined above. 
    This certificate serves as proof of purchase and license ownership.
    <br/><br/>
    <b>Generated by RiffRent Music Platform</b><br/>
    Certificate issued on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
    """

    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=1  # Center alignment
    )

    story.append(Paragraph(footer_text, footer_style))

    # Build PDF
    doc.build(story)

    # Get PDF content
    pdf_content = buffer.getvalue()
    buffer.close()

    # Save to purchase model
    filename = f"license_{purchase.track.title}_{purchase.license_type.name}_{purchase.public_id}.pdf"
    purchase.license_file.save(
        filename,
        ContentFile(pdf_content),
        save=True
    )

    return purchase.license_file.url


# Alternative simpler version using canvas directly
def generate_simple_license_certificate(purchase):
    """Generate a simpler PDF license certificate using canvas"""

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Title
    p.setFont("Helvetica-Bold", 24)
    p.setFillColor(colors.HexColor('#2c3e50'))
    p.drawCentredText(width / 2, height - 100, "MUSIC LICENSE CERTIFICATE")

    # Certificate details
    y_position = height - 150
    p.setFont("Helvetica", 12)

    details = [
        f"Certificate ID: {purchase.public_id}",
        f"Issue Date: {purchase.purchased_at.strftime('%B %d, %Y')}",
        f"License Type: {purchase.license_type.display_name}",
        "",
        "TRACK INFORMATION",
        f"Title: {purchase.track.title}",
        f"Artist: {purchase.track.artist.username}",
        f"Duration: {purchase.track.duration_formatted}",
        "",
        "LICENSE HOLDER",
        f"Name: {purchase.buyer.first_name} {purchase.buyer.last_name}",
        f"Email: {purchase.buyer.email}",
        f"Purchase Date: {purchase.purchased_at.strftime('%B %d, %Y')}",
        f"Amount Paid: ${purchase.price_paid}",
        "",
        "LICENSE PERMISSIONS",
        f"Commercial Use: {'Yes' if purchase.license_type.allows_commercial_use else 'No'}",
        f"Modification: {'Yes' if purchase.license_type.allows_modification else 'No'}",
        f"Attribution Required: {'Yes' if purchase.license_type.requires_attribution else 'No'}",
    ]

    for detail in details:
        if detail == "TRACK INFORMATION" or detail == "LICENSE HOLDER" or detail == "LICENSE PERMISSIONS":
            p.setFont("Helvetica-Bold", 14)
        else:
            p.setFont("Helvetica", 11)
        p.drawString(72, y_position, detail)
        y_position -= 20

    p.showPage()
    p.save()

    # Save to purchase model
    pdf_content = buffer.getvalue()
    buffer.close()

    filename = f"license_{purchase.public_id}.pdf"
    purchase.license_file.save(
        filename,
        ContentFile(pdf_content),
        save=True
    )

    return purchase.license_file.url