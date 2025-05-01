from pathlib import Path
import sys
# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import random

from utils.content_utils import format_category
from agents.content import social_post_agent
from crews.content_crew import generate_social_campaign, schedule_to_buffer


def show_theme_details(theme_slug, theme_data):
    """Show detailed theme information in an expandable section"""
    theme = theme_data[theme_slug]
    
    # Extract metadata
    features = theme.get("features", [])
    selling_points = theme.get("selling_points", [])
    theme_style = theme.get("theme_style", [])
    target_audience = theme.get("target_audience", [])
    testimonials = theme.get("testimonials", [])
    use_cases = theme.get("use_cases", [])
    
    # Create tabs for different sections
    tabs = st.tabs(["Overview", "Features", "Selling Points", "Target Audience", "Testimonials", "Use Cases"])
    
    # Overview tab
    with tabs[0]:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            ## {theme.get('name', '')}
            
            **Category:** {format_category(theme.get('category', ''))}  
            **Builder:** {theme.get('builder', '')}  
            **Version:** {theme.get('version', '')}  
            **Updated:** {theme.get('updated', '')}  
            
            ### Description
            {theme.get('description', '')}
            
            ### Long Description
            {theme.get('longdescription', '')}
            """)
        
        with col2:
            st.markdown(f"""
            ### Links
            **Demo URL:** [{theme.get('demourl', '')}]({theme.get('demourl', '')})  
            **Short Link:** [{theme.get('shortlink', '')}]({theme.get('shortlink', '')})  
            **ThemeForest URL:** [{theme.get('url', '')}]({theme.get('url', '')})
            
            **Item ID:** {theme.get('itemId', '')}
            """)
    
    # Features tab
    with tabs[1]:
        if features:
            for feature in features:
                st.markdown(f"- {feature}")
        else:
            st.info("No features listed for this theme.")
    
    # Selling Points tab
    with tabs[2]:
        if selling_points:
            for point in selling_points:
                st.markdown(f"- {point}")
        else:
            st.info("No selling points listed for this theme.")
    
    # Target Audience tab
    with tabs[3]:
        if target_audience:
            for audience in target_audience:
                st.markdown(f"- {audience}")
        else:
            st.info("No target audience listed for this theme.")
    
    # Testimonials tab
    with tabs[4]:
        if testimonials:
            for testimonial in testimonials:
                with st.container():
                    st.markdown(f"""
                    > "{testimonial.get('text', '')}"
                    >
                    > — *{testimonial.get('author', '')}* ({testimonial.get('rating', '')} stars)
                    """)
        else:
            st.info("No testimonials listed for this theme.")
    
    # Use Cases tab
    with tabs[5]:
        if use_cases:
            for use_case in use_cases:
                st.markdown(f"- {use_case}")
        else:
            st.info("No use cases listed for this theme.")

# Set page config
st.set_page_config(
    page_title="Theme Content Dashboard",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add some custom CSS for better styling
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    h1, h2, h3 {
        color: #2E4057;
    }
    .platform-header {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .post-container {
        background-color: white;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #e6e6e6;
        margin-bottom: 10px;
    }
    .theme-detail {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    .metrics-container {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Main title
st.title("🎨 Theme Content Dashboard")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Theme Explorer", "Content Generator", "Blog Post Generator", "Scheduling", "Analytics"])

# In actual implementation, load from social_post_agent
data = social_post_agent.load_data()
theme_data = data["theme_data"]

# Convert theme data to a DataFrame for easier filtering
theme_df = pd.DataFrame([
    {
        "slug": slug,
        "name": theme.get("name", ""),
        "category": format_category(theme.get("category", "")),
        "builder": theme.get("builder", ""),
        "version": theme.get("version", ""),
        "updated": theme.get("updated", "")
    }
    for slug, theme in theme_data.items()
])

# Theme Explorer page
if page == "Theme Explorer":
    st.header("Theme Explorer")
    
    # Filters in the sidebar
    st.sidebar.header("Filters")
    
    # Category filter
    all_categories = []
    for theme in theme_data.values():
        cat = theme.get("category", "")
        if isinstance(cat, list):
            all_categories.extend(cat)
        elif cat:
            all_categories.append(cat)
    
    unique_categories = sorted(list(set([c for c in all_categories if c])))
    selected_category = st.sidebar.selectbox("Category", ["All"] + unique_categories)
    
    # Builder filter
    builders = sorted(theme_df["builder"].unique().tolist())
    selected_builder = st.sidebar.selectbox("Builder", ["All"] + builders)
    
    # Filter the dataframe
    filtered_df = theme_df.copy()
    if selected_category != "All":
        # Handle both string and list categories
        filtered_df = filtered_df[filtered_df["category"].apply(
            lambda x: selected_category in x if isinstance(x, list) else selected_category == x
        )]
    
    if selected_builder != "All":
        filtered_df = filtered_df[filtered_df["builder"] == selected_builder]
    
    # Display the filtered themes
    st.subheader(f"Showing {len(filtered_df)} themes")
    
    # Theme grid
    cols = st.columns(3)
    for i, (_, theme_row) in enumerate(filtered_df.iterrows()):
        slug = theme_row["slug"]
        theme = theme_data[slug]
        
        with cols[i % 3]:
            with st.container():
                st.markdown(f"""
                <div class="theme-detail">
                    <h3>{theme.get('name', '')}</h3>
                    <p><strong>Category:</strong> {format_category(theme.get('category', ''))}</p>
                    <p><strong>Builder:</strong> {theme.get('builder', '')}</p>
                    <p><strong>Version:</strong> {theme.get('version', '')}</p>
                    <p><strong>Updated:</strong> {theme.get('updated', '')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"View Details: {theme.get('name', '')}", key=f"view_{slug}"):
                    st.session_state.view_theme = slug
                
                # This would open a detailed view in the real app
                if st.button(f"Generate Content: {theme.get('name', '')}", key=f"generate_{slug}"):
                    st.session_state.selected_theme = slug
                    st.session_state.page = "Content Generator"
                    st.experimental_rerun()
    
    # MOVED: Theme details expander - now outside the theme grid loop
    if "view_theme" in st.session_state:
        with st.expander("Theme Details", expanded=True):
            show_theme_details(st.session_state.view_theme, theme_data)
            if st.button("Close"):
                del st.session_state.view_theme

    # Add a statistics panel
    st.sidebar.header("Theme Statistics")
    
    # Calculate stats
    total_themes = len(theme_data)
    themes_by_builder = theme_df.groupby("builder").size().to_dict()
    newest_themes = theme_df.sort_values("updated", ascending=False).head(5)
    
    # Display stats
    st.sidebar.metric("Total Themes", total_themes)
    
    st.sidebar.subheader("Themes by Builder")
    for builder, count in themes_by_builder.items():
        st.sidebar.text(f"{builder}: {count}")
    
    st.sidebar.subheader("Recently Updated")
    for _, row in newest_themes.iterrows():
        st.sidebar.text(f"{row['name']} ({row['updated']})")

# Content Generator page
elif page == "Content Generator":
    st.header("Content Generator")
    
    # Theme selection
    if "selected_theme" not in st.session_state:
        selected_theme = st.selectbox(
            "Select Theme",
            options=theme_df["slug"].tolist(),
            format_func=lambda x: theme_data[x].get("name", x)
        )
        st.session_state.selected_theme = selected_theme
    else:
        selected_theme = st.session_state.selected_theme
        # Fix for the SelectBox value type error
        index_value = theme_df[theme_df["slug"] == selected_theme].index[0]
        if hasattr(index_value, 'item'):  # Check if it's a numpy type that needs conversion
            index_value = index_value.item()  # Convert numpy.int64 to Python int
        else:
            index_value = int(index_value)  # Regular int conversion as fallback
            
        st.selectbox(
            "Select Theme",
            options=theme_df["slug"].tolist(),
            index=index_value,
            format_func=lambda x: theme_data[x].get("name", x),
            key="theme_selector"
        )
    
    # Display theme details
    theme = theme_data[selected_theme]
    st.subheader(f"Generating content for: {theme.get('name', '')}")
    
    with st.expander("Theme Details", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **Category:** {format_category(theme.get('category', ''))}  
            **Builder:** {theme.get('builder', '')}  
            **Version:** {theme.get('version', '')}  
            **Updated:** {theme.get('updated', '')}  
            **Description:** {theme.get('description', '')}
            """)
        
        with col2:
            st.markdown(f"""
            **Demo URL:** [{theme.get('demourl', '')}]({theme.get('demourl', '')})  
            **Short Link:** [{theme.get('shortlink', '')}]({theme.get('shortlink', '')})  
            **ThemeForest URL:** [{theme.get('url', '')}]({theme.get('url', '')})
            """)
    
    # Social media post generation
    st.subheader("Generate Social Media Posts")
    
    col1, col2 = st.columns(2)
    
    with col1:
        platforms = st.multiselect(
            "Select Platforms",
            options=["facebook", "instagram", "x"],
            default=["facebook", "instagram", "x"]
        )

    with st.expander("Advanced Content Options"):
        st.subheader("Content Focus")
        
        # Theme metadata focus
        focus_options = [
            "Balanced (Default)",
            "Feature Focused",
            "Selling Points Focused",
            "Audience Focused",
            "New Release Announcement" if theme.get("updated", "") > (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d") else None,
            "Testimonial Based" if theme.get("testimonials", []) else None
        ]
        focus_options = [opt for opt in focus_options if opt is not None]
        
        selected_focus = st.selectbox(
            "Content Focus",
            options=focus_options
        )
        
        # Custom content adjustments
        st.subheader("Content Adjustments")
        
        emoji_use = st.slider("Emoji Usage", 0, 3, 1, 
                            help="0 = No emojis, 3 = Maximum emojis")
        
        hashtag_density = st.slider("Hashtag Density (Instagram)", 1, 5, 3,
                                help="1 = Minimal hashtags, 5 = Maximum hashtags")
        
        tone_options = ["Professional", "Casual", "Excited", "Informative"]
        selected_tone = st.selectbox("Tone", tone_options)
        
        # Pass these parameters to the generate_social_campaign function
        if st.button("Apply Settings"):
            st.session_state.content_settings = {
                "focus": selected_focus,
                "emoji_use": emoji_use,
                "hashtag_density": hashtag_density,
                "tone": selected_tone
            }
            st.success("Settings applied! They will be used when generating posts.")
    
    with col2:
        post_count = st.slider("Number of Posts per Platform", 1, 5, 2)
    
    if st.button("Generate Posts"):
        with st.spinner("Generating posts..."):
            # Check for content settings
            content_settings = st.session_state.get("content_settings", {})
            
            # In a real implementation, you would pass these settings to your function
            # For now, just use the basic generate_social_campaign function
            posts = generate_social_campaign(selected_theme, platforms, post_count)
            st.session_state.generated_posts = posts
    
    # Display generated posts
    if "generated_posts" in st.session_state:
        posts = st.session_state.generated_posts
        
        st.subheader("Generated Posts")
        
        for platform in posts:
            if platform not in platforms:
                continue
                
            st.markdown(f"<div class='platform-header'>{platform.upper()}</div>", unsafe_allow_html=True)
            
            for i, post in enumerate(posts[platform]):
                with st.container():
                    st.markdown(f"<div class='post-container'>{post}</div>", unsafe_allow_html=True)
                    
                    # Edit button for each post
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        edited_post = st.text_area(f"Edit {platform} post {i+1}", post, key=f"edit_{platform}_{i}")
                        if edited_post != post:
                            st.session_state.generated_posts[platform][i] = edited_post
                    
                    with col2:
                        if st.button(f"Regenerate this post", key=f"regen_{platform}_{i}"):
                            # This would regenerate just this post in a real implementation
                            new_posts = generate_social_campaign(selected_theme, [platform], 1)
                            st.session_state.generated_posts[platform][i] = new_posts[platform][0]
                            st.experimental_rerun()
        
        # Schedule button
        if st.button("Schedule these posts to Buffer"):
            st.session_state.posts_to_schedule = st.session_state.generated_posts
            st.session_state.page = "Scheduling"
            st.experimental_rerun()

# Scheduling page
elif page == "Scheduling":
    st.header("Schedule Posts to Buffer")
    
    if "posts_to_schedule" not in st.session_state:
        st.warning("No posts to schedule. Please generate posts first.")
        if st.button("Go to Content Generator"):
            st.session_state.page = "Content Generator"
            st.experimental_rerun()
    else:
        posts = st.session_state.posts_to_schedule
        
        st.subheader("Posts to Schedule")
        
        # Display the posts
        for platform in posts:
            st.markdown(f"<div class='platform-header'>{platform.upper()}</div>", unsafe_allow_html=True)
            
            for i, post in enumerate(posts[platform]):
                with st.container():
                    st.markdown(f"<div class='post-container'>{post}</div>", unsafe_allow_html=True)
        
        # Scheduling options
        st.subheader("Scheduling Options")
        
        schedule_option = st.radio(
            "Scheduling Method",
            ["Auto-schedule (next 7 days)", "Custom schedule"]
        )
        
        if schedule_option == "Auto-schedule (next 7 days)":
            # Auto scheduling logic
            start_date = st.date_input("Start Date", datetime.now())
            
            # Show the auto-generated schedule
            st.subheader("Auto-generated Schedule")
            
            schedule_times = {}
            auto_schedule_df = pd.DataFrame(columns=["Platform", "Post", "Date", "Time"])
            
            row_index = 0
            for platform in posts:
                platform_times = []
                for i, post in enumerate(posts[platform]):
                    # Schedule each post a day apart
                    post_date = start_date + timedelta(days=i)
                    post_time = "10:00" if platform == "facebook" else "12:00" if platform == "instagram" else "15:00"
                    platform_times.append(f"{post_date} {post_time}")
                    
                    # Add to dataframe for display
                    auto_schedule_df.loc[row_index] = [platform, f"{post[:30]}...", post_date, post_time]
                    row_index += 1
                
                schedule_times[platform] = platform_times
            
            st.table(auto_schedule_df)
            
        else:
            # Custom scheduling logic
            st.write("Set custom times for each post:")
            
            # Create a custom schedule
            schedule_times = {}
            
            for platform in posts:
                st.markdown(f"<div class='platform-header'>{platform.upper()}</div>", unsafe_allow_html=True)
                platform_times = []
                
                for i, post in enumerate(posts[platform]):
                    st.markdown(f"<div class='post-container'>{post[:50]}...</div>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        post_date = st.date_input(f"{platform} Post {i+1} Date", datetime.now() + timedelta(days=i+1), key=f"date_{platform}_{i}")
                    with col2:
                        post_time = st.time_input(f"{platform} Post {i+1} Time", datetime.strptime("10:00", "%H:%M").time(), key=f"time_{platform}_{i}")
                    
                    platform_times.append(f"{post_date} {post_time}")
                
                schedule_times[platform] = platform_times
        
        # Schedule button
        if st.button("Confirm and Schedule to Buffer"):
            with st.spinner("Scheduling posts to Buffer..."):
                # Schedule the posts
                result = schedule_to_buffer(posts, schedule_times)
                
                if result.get("status") == "scheduled":
                    st.success(result.get("message", "Successfully scheduled posts to Buffer"))
                    
                    # Clear the posts to schedule
                    if "posts_to_schedule" in st.session_state:
                        del st.session_state.posts_to_schedule
                else:
                    st.error(f"Error scheduling posts: {result.get('message', 'Unknown error')}")

# Enhanced analytics visualization
elif page == "Analytics":
    st.header("Content Analytics")
    
    # Add tabs for different analytics views
    analytics_tabs = st.tabs(["Platform Metrics", "Theme Performance", "Content Type Performance"])
    
    with analytics_tabs[0]:
        # Platform metrics (existing code)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("<div class='metrics-container'>", unsafe_allow_html=True)
            st.subheader("Facebook")
            st.metric("Reach", random.randint(1000, 5000), "+12%")
            st.metric("Engagement", random.randint(100, 500), "+8%")
            st.metric("Clicks", random.randint(50, 200), "+15%")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='metrics-container'>", unsafe_allow_html=True)
            st.subheader("Instagram")
            st.metric("Reach", random.randint(2000, 8000), "+18%")
            st.metric("Engagement", random.randint(200, 800), "+22%")
            st.metric("Clicks", random.randint(80, 300), "+10%")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown("<div class='metrics-container'>", unsafe_allow_html=True)
            st.subheader("X")
            st.metric("Reach", random.randint(1500, 6000), "+5%")
            st.metric("Engagement", random.randint(150, 600), "+7%")
            st.metric("Clicks", random.randint(60, 250), "+9%")
            st.markdown("</div>", unsafe_allow_html=True)
    
    with analytics_tabs[1]:
        # Theme performance
        st.subheader("Theme Performance")
        
        # Mock theme performance data
        theme_performance = pd.DataFrame({
            "Theme": [t.get("name", slug) for slug, t in list(theme_data.items())[:10]],
            "Clicks": [random.randint(50, 500) for _ in range(10)],
            "Engagement": [random.randint(100, 1000) for _ in range(10)],
            "Conversion Rate": [round(random.uniform(0.5, 5.0), 2) for _ in range(10)]
        })
        
        # Sort by clicks
        theme_performance = theme_performance.sort_values("Clicks", ascending=False)
        
        # Create a bar chart
        st.bar_chart(theme_performance.set_index("Theme")["Clicks"])
        
        # Display the table
        st.table(theme_performance)
    
    with analytics_tabs[2]:
        # Content type performance
        st.subheader("Content Type Performance")
        
        # Mock content type data
        content_types = ["Feature-focused", "Selling Points", "General Announcement"]
        content_performance = pd.DataFrame({
            "Content Type": content_types,
            "Facebook Engagement": [random.randint(50, 200) for _ in range(3)],
            "Instagram Engagement": [random.randint(80, 300) for _ in range(3)],
            "X Engagement": [random.randint(30, 150) for _ in range(3)]
        })
        
        # Display as a bar chart
        st.bar_chart(content_performance.set_index("Content Type"))
        
        # Display the table
        st.table(content_performance)
        
        # Content recommendations
        st.subheader("Content Strategy Recommendations")
        
        st.markdown(f"""
        Based on the performance data, here are some recommendations:
        
        1. **Focus on {content_types[0]}** for Instagram posts (highest engagement)
        2. **Increase post frequency** for top-performing themes like {theme_performance.iloc[0]["Theme"]}
        3. Consider **A/B testing** different content approaches for themes with low engagement
        """)

# Blog Post Generator page
elif page == "Blog Post Generator":
    st.header("Blog Post Generator")
    
    # Theme selection
    selected_theme = st.selectbox(
        "Select Theme",
        options=theme_df["slug"].tolist(),
        format_func=lambda x: theme_data[x].get("name", x)
    )
    
    # Display theme details
    theme = theme_data[selected_theme]
    st.subheader(f"Generating blog post for: {theme.get('name', '')}")
    
    with st.expander("Theme Details", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **Category:** {format_category(theme.get('category', ''))}  
            **Builder:** {theme.get('builder', '')}  
            **Description:** {theme.get('description', '')}
            """)
        
        with col2:
            st.markdown(f"""
            **Demo URL:** [{theme.get('demourl', '')}]({theme.get('demourl', '')})  
            **Short Link:** [{theme.get('shortlink', '')}]({theme.get('shortlink', '')})
            """)
    
    # Blog post options
    st.subheader("Blog Post Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        post_type = st.selectbox(
            "Post Type",
            options=["review", "tutorial", "showcase", "announcement", "comparison"]
        )
    
    with col2:
        word_count = st.slider(
            "Target Word Count",
            min_value=300,
            max_value=2000,
            value=800,
            step=100
        )
    
    # Advanced options
    with st.expander("Advanced Options"):
        include_features = st.checkbox("Include Features", value=True)
        include_testimonials = st.checkbox("Include Testimonials", value=True)
        
        focus_options = [
            "General Overview",
            "Technical Details",
            "Use Cases",
            "Design Aspects",
            "Comparison with Other Themes"
        ]
        post_focus = st.selectbox("Post Focus", focus_options)
        
        seo_keywords = st.text_area("SEO Keywords (one per line)", height=100)
    
    # Generate button
    if st.button("Generate Blog Post"):
        st.session_state.generating_blog = True
        with st.spinner("Generating blog post..."):
            # Here you would call your blog post generator function
            # For demonstration, we'll create a placeholder
            
            # In a real implementation you would do:
            # from crews.content_crew import generate_blog_post
            # blog_post = generate_blog_post(...)
            
            # Mock blog post generation
            blog_post = {
                "title": f"{theme.get('name')} - The Perfect {format_category(theme.get('category', ''))} WordPress Theme",
                "meta_description": f"Discover why {theme.get('name')} is the ideal WordPress theme for your {format_category(theme.get('category', ''))} website. Features, customization options, and more!",
                "content": f"""
                # {theme.get('name')} - The Perfect {format_category(theme.get('category', ''))} WordPress Theme
                
                *Published on {datetime.now().strftime('%B %d, %Y')}*
                
                ## Introduction
                
                Are you looking for a professional WordPress theme for your {format_category(theme.get('category', ''))} website? Look no further than {theme.get('name')}! This theme provides everything you need to create a stunning website with minimal effort.
                
                {theme.get('longdescription', '')}
                
                ## Key Features
                
                {theme.get('name')} comes packed with features that make it stand out from the competition:
                
                {"".join([f'- {feature}\n' for feature in theme.get('features', [])[:5]])}
                
                ## Why Choose {theme.get('name')}?
                
                {theme.get('name')} is designed with {format_category(theme.get('category', ''))} websites in mind. It provides a perfect balance of aesthetics and functionality.
                
                {"".join([f'- {point}\n' for point in theme.get('selling_points', [])[:3]])}
                
                ## Perfect For
                
                {theme.get('name')} is ideal for:
                
                {"".join([f'- {audience}\n' for audience in theme.get('target_audience', [])[:3]])}
                
                ## Customer Testimonials
                
                Don't just take our word for it. Here's what our customers are saying:
                
                {"".join([f'> "{t.get("text")}" - {t.get("author")}\n\n' for t in theme.get('testimonials', [])[:2]])}
                
                ## Conclusion
                
                If you're looking for a {format_category(theme.get('category', ''))} WordPress theme that combines stunning design with powerful features, {theme.get('name')} is an excellent choice. With its user-friendly interface and extensive customization options, you can create a professional website that perfectly represents your brand.
                
                [Check out the demo]({theme.get('demourl', '')}) to see {theme.get('name')} in action!
                """
            }
            
            st.session_state.blog_post = blog_post
            st.session_state.generating_blog = False
    
    # Display generated blog post
    if "blog_post" in st.session_state and not st.session_state.get("generating_blog", False):
        blog_post = st.session_state.blog_post
        
        st.subheader("Generated Blog Post")
        
        # Display SEO info
        with st.expander("SEO Information", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_input("Title", value=blog_post["title"])
            
            with col2:
                st.text_area("Meta Description", value=blog_post["meta_description"], height=100)
        
        # Display blog content
        st.markdown(blog_post["content"])
        
        # Export options
        export_format = st.selectbox("Export Format", ["Markdown", "HTML", "Text"])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Copy to Clipboard"):
                st.success("Blog post copied to clipboard!")
        
        with col2:
            if st.button("Download"):
                file_extension = ".md" if export_format == "Markdown" else ".html" if export_format == "HTML" else ".txt"
                filename = f"{selected_theme}_blog_post{file_extension}"
                st.success(f"Blog post downloaded as {filename}")

# Check if we need to switch pages based on session state
if "page" in st.session_state and st.session_state.page != page:
    # Switch to the page in session state
    st.experimental_rerun()