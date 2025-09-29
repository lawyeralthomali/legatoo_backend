"""
Enjaz Bot for RPA integration.

This module provides the RPA functionality to scrape case data
from the Enjaz system using Playwright.
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, Page
from ..schemas.enjaz_schemas import CaseData


class EnjazBot:
    """Enjaz Bot for automated case data extraction."""
    
    def __init__(self, headless: bool = True):
        """
        Initialize the Enjaz Bot.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def start(self):
        """Start the browser and create a new page."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.page = await self.browser.new_page()
        
        # Set user agent to avoid detection
        await self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    async def close(self):
        """Close the browser and playwright."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
    async def login(self, username: str, password: str) -> bool:
        """
        Login to Enjaz system.
        
        Args:
            username: Enjaz username
            password: Enjaz password
            
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            # Navigate to Enjaz login page
            # Note: Replace with actual Enjaz URL
            await self.page.goto("https://enjaz.gov.sa/login", wait_until="networkidle")
            
            # Fill login form
            await self.page.fill('input[name="username"]', username)
            await self.page.fill('input[name="password"]', password)
            
            # Submit form
            await self.page.click('button[type="submit"]')
            
            # Wait for navigation or error message
            await self.page.wait_for_timeout(3000)
            
            # Check if login was successful
            # Look for dashboard or error message
            current_url = self.page.url
            if "dashboard" in current_url or "home" in current_url:
                return True
            
            # Check for error messages
            error_element = await self.page.query_selector('.error, .alert-danger, .login-error')
            if error_element:
                error_text = await error_element.text_content()
                print(f"Login error: {error_text}")
                return False
            
            return False
            
        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False
    
    async def get_cases(self) -> List[CaseData]:
        """
        Scrape all cases from Enjaz system.
        
        Returns:
            List[CaseData]: List of case data
        """
        try:
            # Navigate to cases page
            # Note: Replace with actual cases URL
            await self.page.goto("https://enjaz.gov.sa/cases", wait_until="networkidle")
            
            # Wait for cases table to load
            await self.page.wait_for_selector('table.cases-table, .case-item', timeout=10000)
            
            # Extract case data
            cases = await self.page.evaluate("""
                () => {
                    const cases = [];
                    
                    // Try different selectors for case items
                    const caseElements = document.querySelectorAll('tr.case-row, .case-item, .case-card');
                    
                    caseElements.forEach((element, index) => {
                        try {
                            // Extract case number
                            const caseNumberElement = element.querySelector('.case-number, .number, [data-case-number]');
                            const caseNumber = caseNumberElement ? caseNumberElement.textContent.trim() : `CASE-${index + 1}`;
                            
                            // Extract case type
                            const caseTypeElement = element.querySelector('.case-type, .type, [data-case-type]');
                            const caseType = caseTypeElement ? caseTypeElement.textContent.trim() : 'Unknown';
                            
                            // Extract status
                            const statusElement = element.querySelector('.status, .state, [data-status]');
                            const status = statusElement ? statusElement.textContent.trim() : 'Unknown';
                            
                            // Additional data
                            const additionalData = {
                                scraped_at: new Date().toISOString(),
                                element_index: index
                            };
                            
                            cases.push({
                                case_number: caseNumber,
                                case_type: caseType,
                                status: status,
                                additional_data: additionalData
                            });
                        } catch (error) {
                            console.error('Error extracting case data:', error);
                        }
                    });
                    
                    return cases;
                }
            """)
            
            # Convert to CaseData objects
            case_data_list = []
            for case in cases:
                case_data = CaseData(
                    case_number=case['case_number'],
                    case_type=case['case_type'],
                    status=case['status'],
                    additional_data=case['additional_data']
                )
                case_data_list.append(case_data)
            
            return case_data_list
            
        except Exception as e:
            print(f"Failed to scrape cases: {str(e)}")
            return []
    
    async def scrape_cases_with_credentials(self, username: str, password: str) -> List[CaseData]:
        """
        Complete workflow: login and scrape cases.
        
        Args:
            username: Enjaz username
            password: Enjaz password
            
        Returns:
            List[CaseData]: List of scraped case data
        """
        try:
            # Login first
            login_success = await self.login(username, password)
            if not login_success:
                raise Exception("Failed to login to Enjaz system")
            
            # Scrape cases
            cases = await self.get_cases()
            return cases
            
        except Exception as e:
            print(f"Scraping failed: {str(e)}")
            return []


async def scrape_enjaz_cases(username: str, password: str, headless: bool = True) -> List[CaseData]:
    """
    Standalone function to scrape Enjaz cases.
    
    Args:
        username: Enjaz username
        password: Enjaz password
        headless: Whether to run browser in headless mode
        
    Returns:
        List[CaseData]: List of scraped case data
    """
    async with EnjazBot(headless=headless) as bot:
        return await bot.scrape_cases_with_credentials(username, password)
