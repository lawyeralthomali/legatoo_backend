"""
Script to create subscription plans and subscriptions for existing users.
Run this to ensure there's a free plan and that all users have subscriptions.
"""
import asyncio
import sys
import os

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import AsyncSessionLocal
from app.models.plan import Plan
from app.models.subscription import Subscription, StatusType
from app.models.profile import Profile
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def create_plans(db: AsyncSession):
    """Create subscription plans if they don't exist."""
    print("📦 Checking for plans...")
    
    # Check if free plan exists
    result = await db.execute(
        select(Plan).where(Plan.plan_type == "free").where(Plan.is_active == True)
    )
    free_plan = result.scalar_one_or_none()
    
    if not free_plan:
        print("➕ Creating free plan...")
        free_plan = Plan(
            plan_name="Free Trial",
            plan_type="free",
            price=0.00,
            billing_cycle="none",
            file_limit=10,
            ai_message_limit=50,
            contract_limit=5,
            report_limit=3,
            token_limit=10000,
            multi_user_limit=1,
            description="Free trial plan with limited features",
            is_active=True
        )
        db.add(free_plan)
        await db.commit()
        await db.refresh(free_plan)
        print(f"✅ Created free plan (ID: {free_plan.plan_id})")
    else:
        print(f"✅ Free plan already exists (ID: {free_plan.plan_id})")
    
    # Check for monthly plan
    result = await db.execute(
        select(Plan).where(Plan.plan_type == "monthly").where(Plan.is_active == True)
    )
    monthly_plan = result.scalar_one_or_none()
    
    if not monthly_plan:
        print("➕ Creating monthly plan...")
        monthly_plan = Plan(
            plan_name="Monthly Plan",
            plan_type="monthly",
            price=99.00,
            billing_cycle="monthly",
            file_limit=100,
            ai_message_limit=500,
            contract_limit=50,
            report_limit=30,
            token_limit=100000,
            multi_user_limit=5,
            description="Monthly subscription plan",
            is_active=True
        )
        db.add(monthly_plan)
        await db.commit()
        await db.refresh(monthly_plan)
        print(f"✅ Created monthly plan (ID: {monthly_plan.plan_id})")
    else:
        print(f"✅ Monthly plan already exists (ID: {monthly_plan.plan_id})")
    
    # Check for annual plan
    result = await db.execute(
        select(Plan).where(Plan.plan_type == "annual").where(Plan.is_active == True)
    )
    annual_plan = result.scalar_one_or_none()
    
    if not annual_plan:
        print("➕ Creating annual plan...")
        annual_plan = Plan(
            plan_name="Annual Plan",
            plan_type="annual",
            price=999.00,
            billing_cycle="yearly",
            file_limit=1000,
            ai_message_limit=5000,
            contract_limit=500,
            report_limit=300,
            token_limit=1000000,
            multi_user_limit=20,
            description="Annual subscription plan with best value",
            is_active=True
        )
        db.add(annual_plan)
        await db.commit()
        await db.refresh(annual_plan)
        print(f"✅ Created annual plan (ID: {annual_plan.plan_id})")
    else:
        print(f"✅ Annual plan already exists (ID: {annual_plan.plan_id})")
    
    return free_plan


async def create_subscriptions_for_existing_users(db: AsyncSession, free_plan: Plan):
    """Create subscriptions for users who don't have one."""
    print("\n👥 Checking for users without subscriptions...")
    
    # Get all profiles
    result = await db.execute(select(Profile))
    profiles = result.scalars().all()
    
    created_count = 0
    skipped_count = 0
    
    for profile in profiles:
        # Check if profile already has a subscription
        sub_result = await db.execute(
            select(Subscription).where(Subscription.user_id == profile.id)
        )
        existing_sub = sub_result.scalar_one_or_none()
        
        if not existing_sub:
            # Create subscription for this user
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=7)  # 7-day free trial
            
            subscription = Subscription(
                user_id=profile.id,
                plan_id=free_plan.plan_id,
                start_date=start_date,
                end_date=end_date,
                status=StatusType.ACTIVE,
                auto_renew=False
            )
            
            db.add(subscription)
            created_count += 1
            print(f"  ✅ Created subscription for: {profile.email}")
        else:
            skipped_count += 1
    
    if created_count > 0:
        await db.commit()
        print(f"\n✅ Created {created_count} new subscriptions")
    
    if skipped_count > 0:
        print(f"⏭️  Skipped {skipped_count} users (already have subscriptions)")
    
    return created_count


async def main():
    """Main function to seed plans and create subscriptions."""
    print("=" * 60)
    print("  Plan and Subscription Creation Script")
    print("=" * 60)
    print()
    
    print(f"📡 Connecting to database...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Create plans
            free_plan = await create_plans(db)
            
            # Create subscriptions for existing users
            await create_subscriptions_for_existing_users(db, free_plan)
            
            print("\n" + "=" * 60)
            print("✨ All done! Plans and subscriptions are ready.")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            await db.rollback()


if __name__ == "__main__":
    asyncio.run(main())

