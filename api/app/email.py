import resend
from app.config import settings


def init_resend():
    print(f"=== RESEND INIT ===")
    print(f"API Key present: {bool(settings.resend_api_key)}")
    print(f"From email: {settings.from_email}")
    print(f"===================")
    resend.api_key = settings.resend_api_key


def send_confirmation_email(to_email: str, name: str, token: str):
    """Send subscription confirmation email."""
    confirm_url = f"{settings.base_url}/confirm?token={token}"
    
    print(f"=== SENDING EMAIL ===")
    print(f"To: {to_email}")
    print(f"URL: {confirm_url}")
    
    try:
        result = resend.Emails.send({
            "from": settings.from_email,
            "to": to_email,
            "subject": "Confirm your NeuralGraph subscription",
            "html": f"""
            <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #10b981;">Welcome to NeuralGraph!</h2>
                <p>Hi {name},</p>
                <p>Thanks for subscribing to our newsletter. Please confirm your email address by clicking the button below:</p>
                <p style="margin: 30px 0;">
                    <a href="{confirm_url}" 
                       style="background: linear-gradient(to right, #10b981, #06b6d4); 
                              color: #000; 
                              padding: 12px 24px; 
                              text-decoration: none; 
                              border-radius: 8px;
                              font-weight: bold;">
                        Confirm Subscription
                    </a>
                </p>
                <p style="color: #666; font-size: 14px;">
                    Or copy this link: <br>
                    <a href="{confirm_url}">{confirm_url}</a>
                </p>
                <p style="color: #666; font-size: 12px; margin-top: 40px;">
                    If you didn't subscribe, you can safely ignore this email.
                </p>
            </div>
            """
        })
        print(f"Resend result: {result}")
        return result
    except Exception as e:
        print(f"Resend error: {e}")
        raise
