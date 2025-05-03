from utils.trading_knowledge_base import TradingKnowledgeBase
from tools.alphavantage_data import AlphaVantageDataTool
from tools.alphavantage_historical import AlphaVantageHistoricalTool
from utils.pdf_framework_reader import DailyBiasFramework

class MarketToolsIntegration:
    """
    A simple integration helper to connect knowledge sources and market data tools
    with the crew agents.
    """
    
    def __init__(self):
        """Initialize the market tools integration"""
        # Initialize components as None initially
        self.knowledge_base = None
        self.framework_reader = None
        self.alpha_vantage = None
        self.alpha_vantage_historical = None
        
        # Track what's available
        self.has_knowledge_base = False
        self.has_framework_reader = False
        self.has_price_data = False
        self.has_historical_data = False
        
        # Try to initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all components and track what's available"""
        # Try to initialize the markdown knowledge base
        try:
            self.knowledge_base = TradingKnowledgeBase()
            self.has_knowledge_base = len(self.knowledge_base.markdown_docs) > 0
            print(f"Knowledge base initialized with {len(self.knowledge_base.markdown_docs)} documents")
        except Exception as e:
            print(f"Error initializing knowledge base: {e}")
            self.has_knowledge_base = False
        
        # Try to initialize the PDF framework reader
        try:
            self.framework_reader = DailyBiasFramework()
            # Check if at least one framework loaded successfully
            self.has_framework_reader = len(self.framework_reader.frameworks) > 0
            print(f"Framework reader initialized with {len(self.framework_reader.frameworks)} frameworks")
        except Exception as e:
            print(f"Error initializing framework reader: {e}")
            self.has_framework_reader = False
        
        # Try to initialize AlphaVantage API tools
        try:
            # Initialize the current price data tool
            self.alpha_vantage = AlphaVantageDataTool()
            # Test the API with a simple request
            rate_data = self.alpha_vantage.get_forex_rate("EUR", "USD")
            self.has_price_data = "error" not in rate_data
            if self.has_price_data:
                print(f"AlphaVantage price data available, current EUR/USD rate: {rate_data['exchange_rate']:.5f}")
                
                # Initialize the historical data tool with the same API key
                self.alpha_vantage_historical = AlphaVantageHistoricalTool()
                self.has_historical_data = True
                print("AlphaVantage historical data tool initialized")
            else:
                print(f"AlphaVantage API error: {rate_data.get('error')}")
        except Exception as e:
            print(f"Error initializing AlphaVantage: {e}")
            self.has_price_data = False
            self.has_historical_data = False
    
    def get_agent_context(self, agent_type):
        """
        Get combined context for a specific agent type
        
        Args:
            agent_type (str): Type of agent ('daily_bias', 'weekly_profile', 'technical', etc.)
            
        Returns:
            str: Combined context from all available sources
        """
        context_parts = []
        
        # Add framework context if available
        if self.has_framework_reader and self.framework_reader:
            if agent_type == 'daily_bias':
                framework = self.framework_reader.get_framework_summary("daily_bias")
                if framework:
                    context_parts.append(framework)
            elif agent_type == 'weekly_profile':
                framework = self.framework_reader.get_framework_summary("weekly_profile")
                if framework:
                    context_parts.append(framework)
            else:
                # Add general framework context for other agent types
                framework = self.framework_reader.get_all_frameworks_context()
                if framework:
                    context_parts.append(framework)
        
        # Add knowledge base context if available
        if self.has_knowledge_base and self.knowledge_base:
            kb_context = self.knowledge_base.get_context_for_agent(agent_type)
            if kb_context:
                context_parts.append(kb_context)
        
        # Add price data if available
        if self.has_price_data and self.alpha_vantage:
            try:
                price_context = self.alpha_vantage.get_price_data_context("EUR", "USD")
                if price_context:
                    context_parts.append(price_context)
                    
                # Add historical context for weekly and technical agents
                if self.has_historical_data and self.alpha_vantage_historical and agent_type in ['weekly_profile', 'technical']:
                    weekly_context = self.alpha_vantage_historical.get_weekly_range_data("EUR", "USD")
                    if weekly_context:
                        # Convert the markdown to plain text for context
                        plain_weekly = weekly_context.replace('###', '').replace('##', '').replace('**', '')
                        context_parts.append(plain_weekly)
            except Exception as e:
                print(f"Error getting price context: {e}")
        
        # Combine all context parts
        if context_parts:
            return "\n\n".join(context_parts)
        else:
            return "No context available."
    
    def enhance_agent(self, agent, agent_type):
        """
        Enhance an agent with context and tools
        
        Args:
            agent: The CrewAI agent to enhance
            agent_type (str): Type of agent
            
        Returns:
            The enhanced agent
        """
        # Add context to agent's backstory
        if hasattr(agent, 'backstory'):
            context = self.get_agent_context(agent_type)
            original_backstory = agent.backstory
            
            # Add context to backstory
            if not original_backstory.endswith('\n'):
                original_backstory += '\n'
            
            agent.backstory = original_backstory + "\n\nKNOWLEDGE CONTEXT:\n" + context
            print(f"Enhanced {agent_type} agent with context ({len(context)} chars)")
        
        # Add tools to agent if available and the agent has a tools attribute
        if hasattr(agent, 'tools'):
            # Start with existing tools or empty list
            current_tools = list(agent.tools) if agent.tools else []
            tools_added = False
            
            # Get current tool names
            current_tool_names = [t.name if hasattr(t, 'name') else str(t) for t in current_tools]
            
            # Add AlphaVantage price data tool
            if self.has_price_data and self.alpha_vantage and self.alpha_vantage.name not in current_tool_names:
                current_tools.append(self.alpha_vantage)
                tools_added = True
                print(f"Added AlphaVantage price data tool to {agent_type} agent")
            
            # Add historical data tool for specific agent types
            if self.has_historical_data and self.alpha_vantage_historical and agent_type in ['technical', 'weekly_profile'] and self.alpha_vantage_historical.name not in current_tool_names:
                current_tools.append(self.alpha_vantage_historical)
                tools_added = True
                print(f"Added AlphaVantage historical data tool to {agent_type} agent")
            
            # Update agent tools if any were added
            if tools_added:
                agent.tools = current_tools
        
        return agent
    
    def get_available_tools(self):
        """
        Get a list of all available tools
        
        Returns:
            list: List of available tools
        """
        tools = []
        
        if self.has_price_data and self.alpha_vantage:
            tools.append(self.alpha_vantage)
            
        if self.has_historical_data and self.alpha_vantage_historical:
            tools.append(self.alpha_vantage_historical)
            
        return tools
    
    def get_agent_map(self):
        """
        Get a mapping of agent instances to their types for easy enhancement
        
        Returns:
            dict: Mapping of {agent_instance: agent_type}
        """
        # Import the agent instances here to avoid circular imports
        try:
            from agents.market.daily_bias_analyst_agent import daily_bias_analyst_agent
            from agents.market.weekly_profile_analyst_agent import weekly_profile_analyst_agent
            from agents.market.technical_analyst_agent import technical_analyst_agent
            from agents.market.fundamental_analyst_agent import fundamental_analyst_agent
            from agents.market.sentiment_analyst_agent import sentiment_analyst_agent
            from agents.market.daily_report_writer_agent import daily_report_writer_agent
            from agents.market.weekly_report_writer_agent import weekly_report_writer_agent
            
            # Create the mapping
            return {
                daily_bias_analyst_agent: 'daily_bias',
                weekly_profile_analyst_agent: 'weekly_profile',
                technical_analyst_agent: 'technical',
                fundamental_analyst_agent: 'fundamental',
                sentiment_analyst_agent: 'sentiment',
                daily_report_writer_agent: 'report_writer',
                weekly_report_writer_agent: 'report_writer'
            }
        except ImportError as e:
            print(f"Error importing agents: {e}")
            return {}

# Test the integration if run directly
if __name__ == "__main__":
    integration = MarketToolsIntegration()
    
    # Test getting context for different agent types
    for agent_type in ['daily_bias', 'weekly_profile', 'technical', 'fundamental']:
        context = integration.get_agent_context(agent_type)
        print(f"\n{agent_type.upper()} AGENT CONTEXT:")
        print(f"  Length: {len(context)} characters")
        print(f"  Preview: {context[:150]}...")
        
    # List available tools
    tools = integration.get_available_tools()
    print(f"\nAvailable tools: {[t.name for t in tools]}")