import json
from deepresearch.tools import (
    plan_research,
    search_web,
    scrape_page,
    analyze_sources,
    generate_final_report,
    save_research
)

def run_deep_research(topic: str, groq_key_fn=None, tavily_key_fn=None) -> str:
    """Execute a full deep research workflow automatically."""
    
    # 1. Plan Research
    plan = plan_research(topic, groq_key_fn=groq_key_fn)
    sub_questions = plan if isinstance(plan, list) else plan.get("sub_questions", [])
    if not isinstance(sub_questions, list) or not sub_questions:
        sub_questions = [
            f"What is the current state of {topic}?",
            f"What are the implications and impact of {topic}?",
            f"Who are the key players regarding {topic}?",
            f"What is the historical context of {topic}?",
            f"What are the future trends for {topic}?",
        ]
    
    research_data = {}
    
    # 2. Iterate over sub-questions
    for question in sub_questions:
        try:
            # Condense question into optimized search query
            from deepresearch.utils import call_llm
            optimized_query = call_llm(
                f"Extract only the 3-5 most important keywords from this question for a search engine query: '{question}'",
                "You are an SEO expert. Reply only with the search keywords, no quotes, no extra text.",
                groq_key_fn=groq_key_fn
            )
            if "GROQ_API_KEY not found." in optimized_query:
                raise ValueError(optimized_query)
            print(f"Original question: {question} -> Optimized query: {optimized_query}")
            
            # Search web
            initial_search = search_web(optimized_query, tavily_key_fn=tavily_key_fn)
            
            urls_with_titles = []
            if isinstance(initial_search, list):
                urls_with_titles = [(res.get('url'), res.get('title', 'Unknown Title')) for res in initial_search if isinstance(res, dict) and 'url' in res][:2]
            elif isinstance(initial_search, dict) and 'results' in initial_search:
                urls_with_titles = [(res.get('url'), res.get('title', 'Unknown Title')) for res in initial_search['results'] if isinstance(res, dict) and 'url' in res][:2]
            else:
                pass # Depending on exactly what search_web returns
                
            scraped_contents = []
            for url, title in urls_with_titles:
                if url:
                    try:
                        content = scrape_page(url)
                        scraped_contents.append({"url": url, "title": title, "content": content})
                    except Exception as e:
                        print(f"Error scraping {url}: {e}")
            
            research_data[question] = {
                "search_results": initial_search,
                "scraped_contents": scraped_contents
            }
        except Exception as e:
            print(f"Error processing question '{question}': {e}")
            research_data[question] = {"error": str(e)}
    
    # 3. Analyze sources
    all_sources = []
    for q, data in research_data.items():
        if "scraped_contents" in data:
            all_sources.extend(data["scraped_contents"])
        elif "search_results" in data:
            sr = data["search_results"]
            if isinstance(sr, list):
                all_sources.extend(sr)
            elif isinstance(sr, dict) and "results" in sr:
                all_sources.extend(sr["results"])
                
    analysis = analyze_sources(topic, all_sources, groq_key_fn=groq_key_fn)
    
    # 4. Generate final report
    report = generate_final_report({
        "topic": topic,
        "analysis": analysis,
        "sub_questions": sub_questions,
        "sources": all_sources
    })
    
    # 5. Save research
    saved_info = save_research(topic, report)
    # Read the saved markdown file
    report_path = saved_info.get('report_path')
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
    except Exception:
        report_content = report
    
    # 6. Return summary
    return json.dumps({
        "status": "completed",
        "topic": topic,
        "steps_completed": len(sub_questions),
        "sources_found": len(all_sources),
        "report_path": report_path,
        "report_content": report_content
    }, indent=2)
