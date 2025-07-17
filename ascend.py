# Ascend - Local Opportunity Connector AI Agent
# SDG 8: Decent Work and Economic Growth
# Real-time Job Search System with AI Recommendations

import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import warnings
warnings.filterwarnings('ignore')

class AscendAIAgent:
    def __init__(self):
        self.job_data = []
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        self.job_vectors = None
        
        self.GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
        self.ADZUNA_APP_ID = "YOUR_ADZUNA_APP_ID"
        self.ADZUNA_APP_KEY = "YOUR_ADZUNA_APP_KEY"
        self.RAPIDAPI_KEY = "YOUR_RAPIDAPI_KEY"
        
    def test_gemini_connection(self):
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.GEMINI_API_KEY)
            
            print("Testing Gemini API connection...")
            
            print("\nAvailable Gemini models:")
            models = genai.list_models()
            
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    print(f"Available: {model.name}")
                else:
                    print(f"Not supported: {model.name}")
            
            model_names = [
                'gemini-1.5-flash',
                'gemini-1.5-pro', 
                'gemini-pro'
            ]
            
            for model_name in model_names:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content("Say 'Hello, this is a test!'")
                    print(f"\n{model_name} is working!")
                    print(f"Response: {response.text}")
                    return True
                except Exception as e:
                    print(f"{model_name} failed: {str(e)}")
                    continue
            
            return False
            
        except Exception as e:
            print(f"Gemini API connection failed: {e}")
            return False
        
    def fetch_real_time_jobs(self, location, skills_query=""):
        print(f"Searching for jobs in {location}...")
        
        jobs = []
        
        jobs.extend(self.fetch_from_adzuna(location, skills_query))
        jobs.extend(self.fetch_from_jsearch(location, skills_query))
        jobs.extend(self.scrape_local_jobs(location, skills_query))
        
        self.job_data = jobs
        print(f"Found {len(self.job_data)} opportunities!")
        return self.job_data
    
    def fetch_from_adzuna(self, location, skills_query):
        try:
            url = f"https://api.adzuna.com/v1/api/jobs/in/search/1"
            params = {
                'app_id': self.ADZUNA_APP_ID,
                'app_key': self.ADZUNA_APP_KEY,
                'results_per_page': 10,
                'what': skills_query,
                'where': location,
                'sort_by': 'date',
                'max_days_old': 7
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                jobs = []
                
                for result in data.get('results', []):
                    job = {
                        'title': result.get('title', ''),
                        'company': result.get('company', {}).get('display_name', ''),
                        'location': result.get('location', {}).get('display_name', ''),
                        'description': result.get('description', ''),
                        'url': result.get('redirect_url', ''),
                        'salary': f"₹{result.get('salary_min', 0)}-{result.get('salary_max', 0)}" if result.get('salary_min') else 'Not specified',
                        'posted_date': result.get('created', ''),
                        'source': 'Adzuna'
                    }
                    jobs.append(job)
                
                return jobs
            
        except Exception as e:
            print(f"Error fetching from Adzuna: {e}")
        
        return []
    
    def fetch_from_jsearch(self, location, skills_query):
        try:
            url = "https://jsearch.p.rapidapi.com/search"
            
            querystring = {
                "query": f"{skills_query} in {location}",
                "page": "1",
                "num_pages": "1",
                "date_posted": "week"
            }
            
            headers = {
                "X-RapidAPI-Key": self.RAPIDAPI_KEY,
                "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
            }
            
            response = requests.get(url, headers=headers, params=querystring, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                jobs = []
                
                for result in data.get('data', []):
                    job = {
                        'title': result.get('job_title', ''),
                        'company': result.get('employer_name', ''),
                        'location': result.get('job_city', '') + ', ' + result.get('job_state', ''),
                        'description': result.get('job_description', ''),
                        'url': result.get('job_apply_link', ''),
                        'salary': result.get('job_salary', 'Not specified'),
                        'posted_date': result.get('job_posted_at_datetime_utc', ''),
                        'source': 'JSearch'
                    }
                    jobs.append(job)
                
                return jobs
            
        except Exception as e:
            print(f"Error fetching from JSearch: {e}")
        
        return []
    
    def scrape_local_jobs(self, location, skills_query):
        try:
            jobs = []
            return jobs
            
        except Exception as e:
            print(f"Error scraping local jobs: {e}")
        
        return []
    
    def prepare_job_vectors(self):
        if not self.job_data:
            print("No job data available. Please fetch jobs first.")
            return
        
        job_texts = []
        for job in self.job_data:
            combined_text = f"{job['title']} {job['description']}"
            job_texts.append(combined_text)
        
        self.job_vectors = self.vectorizer.fit_transform(job_texts)
        print("Job vectors prepared for matching!")
    
    def calculate_skill_relevance(self, user_skills, job_text):
        user_skills_list = [skill.strip().lower() for skill in user_skills.split(',')]
        job_text_lower = job_text.lower()
        
        matches = 0
        for skill in user_skills_list:
            if skill in job_text_lower:
                matches += 1
        
        return (matches / len(user_skills_list)) * 100 if user_skills_list else 0
    
    def find_opportunities(self, user_skills, location, experience_level="entry"):
        print(f"Finding opportunities for:")
        print(f"Location: {location}")
        print(f"Skills: {user_skills}")
        print(f"Experience: {experience_level}")
        print("-" * 50)
        
        jobs = self.fetch_real_time_jobs(location, user_skills)
        
        if not jobs:
            print("No opportunities found in your area.")
            return []
        
        self.prepare_job_vectors()
        
        user_query = f"{user_skills} {location}"
        user_vector = self.vectorizer.transform([user_query])
        
        similarities = cosine_similarity(user_vector, self.job_vectors)[0]
        
        ranked_opportunities = []
        for i, job in enumerate(jobs):
            job_text = f"{job['title']} {job['description']}"
            skill_relevance = self.calculate_skill_relevance(user_skills, job_text)
            
            combined_score = (similarities[i] * 0.7) + (skill_relevance/100 * 0.3)
            
            ranked_opportunities.append({
                'job': job,
                'match_score': combined_score,
                'skill_relevance': skill_relevance
            })
        
        ranked_opportunities.sort(key=lambda x: x['match_score'], reverse=True)
        
        return ranked_opportunities
    
    def display_opportunities(self, opportunities):
        if not opportunities:
            print("No matching opportunities found.")
            return
        
        print(f"Found {len(opportunities)} matching opportunities!")
        print()
        
        for i, opp in enumerate(opportunities[:5], 1):
            job = opp['job']
            match_score = opp['match_score']
            skill_relevance = opp['skill_relevance']
            
            print(f"OPPORTUNITY #{i}")
            print("-" * 40)
            print(f"Job Title: {job['title']}")
            print(f"Company: {job['company']}")
            print(f"Location: {job['location']}")
            print(f"Salary: {job['salary']}")
            print(f"Posted: {job['posted_date']}")
            print(f"Source: {job['source']}")
            print(f"Match Score: {match_score:.1%}")
            print(f"Skill Relevance: {skill_relevance:.1f}%")
            print(f"Description: {job['description'][:200]}...")
            print(f"Apply: {job['url']}")
            print()
    
    def get_upskilling_suggestions(self, user_skills, opportunities):
        if not opportunities:
            return []
        
        skill_keywords = []
        for opp in opportunities[:3]:
            job_text = f"{opp['job']['title']} {opp['job']['description']}"
            words = re.findall(r'\b[A-Za-z]+\b', job_text.lower())
            skill_keywords.extend(words)
        
        from collections import Counter
        common_skills = Counter(skill_keywords).most_common(20)
        
        user_skills_list = [skill.strip().lower() for skill in user_skills.split(',')]
        
        stop_words = {'and', 'the', 'for', 'with', 'or', 'in', 'on', 'at', 'to', 'of', 'a', 'an', 
                     'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 
                     'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 
                     'shall', 'this', 'that', 'these', 'those', 'we', 'you', 'they', 'he', 'she', 
                     'it', 'i', 'me', 'us', 'them', 'him', 'her', 'my', 'your', 'our', 'their', 
                     'his', 'its', 'auction', 'experience', 'work', 'working', 'job', 'position',
                     'role', 'team', 'company', 'business', 'years', 'skills', 'knowledge'}
        
        suggested_skills = []
        for skill, count in common_skills:
            if (skill not in user_skills_list and 
                len(skill) > 2 and 
                skill not in stop_words and
                count >= 2):
                suggested_skills.append(skill.title())
        
        if suggested_skills and len(suggested_skills) > 0:
            print("UPSKILLING SUGGESTIONS:")
            print("Based on current job market demands, consider learning:")
            for skill in suggested_skills[:5]:
                print(f"- {skill}")
            print()
            print("Recommended learning resources:")
            print("- Online courses (Coursera, Udemy, edX)")
            print("- Local training centers")
            print("- YouTube tutorials")
            print("- Professional certifications")
        else:
            print("UPSKILLING SUGGESTIONS:")
            print("Your skills align well with current opportunities!")
            print("Consider deepening your expertise in your existing skills.")
        
        return suggested_skills
    
    def get_ai_recommendations(self, user_skills, opportunities, experience_level="entry"):
        if not opportunities:
            return "No job opportunities found to analyze."
        
        print("\nGenerating AI recommendations...")
        print("=" * 60)
        
        job_analysis = self.prepare_job_analysis(opportunities[:5])
        
        recommendations = self.generate_chat_recommendations(user_skills, job_analysis, experience_level)
        
        print("\nAI CAREER COACH RECOMMENDATIONS:")
        print("=" * 60)
        print(recommendations)
        print("=" * 60)
        
        return recommendations
    
    def prepare_job_analysis(self, opportunities):
        job_summaries = []
        
        for i, opp in enumerate(opportunities, 1):
            job = opp['job']
            
            job_summary = {
                'position': i,
                'title': job['title'],
                'company': job['company'],
                'description': job['description'][:300],
                'match_score': opp['match_score'],
                'skill_relevance': opp['skill_relevance']
            }
            job_summaries.append(job_summary)
        
        return job_summaries
    
    def generate_chat_recommendations(self, user_skills, job_analysis, experience_level):
        try:
            jobs_text = ""
            for job in job_analysis:
                jobs_text += f"\n{job['position']}. {job['title']} at {job['company']}\n"
                jobs_text += f"   Match Score: {job['match_score']:.1%}\n"
                jobs_text += f"   Description: {job['description']}\n"
            
            prompt = f"""
You are an expert career coach and resume advisor. Analyze the following job opportunities and provide personalized recommendations.

USER PROFILE:
- Current Skills: {user_skills}
- Experience Level: {experience_level}

TOP JOB OPPORTUNITIES:
{jobs_text}

Please provide:

1. RESUME OPTIMIZATION TIPS:
   - What keywords should be emphasized in the resume
   - How to highlight relevant experience
   - What skills to prioritize in the skills section
   - Suggestions for resume formatting and structure

2. APPLICATION STRATEGY:
   - Which jobs to prioritize based on match scores
   - How to tailor applications for each role
   - Key points to emphasize in cover letters
   - Interview preparation tips

3. SKILL DEVELOPMENT PLAN:
   - Missing skills that appear frequently in job descriptions
   - Priority order for learning new skills
   - Specific course recommendations with platforms
   - Timeline for skill development

4. INDUSTRY INSIGHTS:
   - Current market trends in these roles
   - Salary negotiation tips
   - Career growth opportunities

Keep the advice practical, actionable, and encouraging. Focus on immediate steps the user can take to improve their job prospects.
"""
            
            recommendations = self.call_gemini_api(prompt)
            
            if not recommendations:
                recommendations = self.generate_fallback_recommendations(user_skills, job_analysis, experience_level)
            
            return recommendations
            
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return self.generate_fallback_recommendations(user_skills, job_analysis, experience_level)
    
    def call_gemini_api(self, prompt):
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.GEMINI_API_KEY)
            
            model_names = [
                'gemini-1.5-flash',
                'gemini-1.5-pro',
                'gemini-pro',
                'models/gemini-pro'
            ]
            
            for model_name in model_names:
                try:
                    model = genai.GenerativeModel(model_name)
                    
                    system_prompt = "You are an expert career coach and resume advisor helping job seekers improve their prospects. Provide practical, actionable advice."
                    
                    full_prompt = f"{system_prompt}\n\n{prompt}"
                    
                    response = model.generate_content(full_prompt)
                    
                    print(f"Successfully used model: {model_name}")
                    return response.text
                    
                except Exception as model_error:
                    print(f"Model {model_name} failed: {str(model_error)}")
                    continue
            
            print("All Gemini models failed")
            return None
            
        except Exception as e:
            print(f"Gemini API error: {e}")
            return None
    
    def generate_fallback_recommendations(self, user_skills, job_analysis, experience_level):
        user_skills_list = [skill.strip().lower() for skill in user_skills.split(',')]
        
        all_descriptions = " ".join([job['description'] for job in job_analysis])
        common_keywords = re.findall(r'\b[A-Za-z]+\b', all_descriptions.lower())
        
        from collections import Counter
        keyword_counts = Counter(common_keywords)
        
        missing_skills = []
        for keyword, count in keyword_counts.most_common(20):
            if len(keyword) > 2 and keyword not in user_skills_list:
                missing_skills.append(keyword.title())
        
        recommendations = f"""
1. RESUME OPTIMIZATION TIPS:
   - Emphasize these keywords in your resume: {', '.join(missing_skills[:5])}
   - Highlight your experience with: {user_skills}
   - Use action verbs like "developed", "implemented", "managed"
   - Keep resume to 1-2 pages and use ATS-friendly format

2. APPLICATION STRATEGY:
   - Apply to jobs with match scores above 70% first
   - Tailor your resume for each application
   - Write compelling cover letters mentioning specific company names
   - Follow up after 1 week if no response

3. SKILL DEVELOPMENT PLAN:
   Priority skills to learn: {', '.join(missing_skills[:5])}
   
   Recommended courses:
   - Coursera: Search for courses on {missing_skills[0] if missing_skills else 'relevant skills'}
   - Udemy: Practical tutorials on {missing_skills[1] if len(missing_skills) > 1 else 'technical skills'}
   - edX: Professional certificates in your field
   - YouTube: Free tutorials for quick learning

4. INDUSTRY INSIGHTS:
   - {experience_level.title()} level positions are in demand
   - Remote work opportunities are increasing
   - Focus on continuous learning and certifications
   - Network with professionals in your target companies

Next Steps:
1. Update your resume with suggested keywords
2. Start learning the top 2 missing skills
3. Apply to the highest-matching jobs first
4. Set up job alerts for similar positions
"""
        
        return recommendations

def interactive_search():
    agent = AscendAIAgent()
    
    print("ASCEND - LOCAL OPPORTUNITY CONNECTOR")
    print("SDG 8: Decent Work and Economic Growth")
    print("=" * 50)
    
    while True:
        print()
        print("Enter your details:")
        user_skills = input("Your skills (comma-separated): ").strip()
        location = input("Your location: ").strip()
        experience = input("Experience level (entry/mid/senior) [entry]: ").strip() or "entry"
        
        if not user_skills or not location:
            print("Please enter both skills and location!")
            continue
        
        opportunities = agent.find_opportunities(user_skills, location, experience)
        
        agent.display_opportunities(opportunities)
        
        if opportunities:
            agent.get_upskilling_suggestions(user_skills, opportunities)
        
        if opportunities:
            print("\nWould you like personalized AI recommendations for resume optimization and career strategy?")
            get_recommendations = input("Get AI recommendations? (y/n): ").strip().lower()
            
            if get_recommendations == 'y':
                agent.get_ai_recommendations(user_skills, opportunities, experience)
        
        another = input("\nSearch again? (y/n): ").strip().lower()
        if another != 'y':
            break
    
    print("Thank you for using Ascend AI Agent!")

if __name__ == "__main__":
    interactive_search()