from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("supabase.env")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Create Supabase client
def get_supabase_client() -> Client:
    """Get Supabase client instance."""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise ValueError("Supabase URL and ANON KEY must be set in environment variables")
    
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Global Supabase client instance
supabase: Client = get_supabase_client()





