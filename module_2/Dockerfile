FROM python:3.12-slim

WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    curl \
    git \
    bash \
    ca-certificates \
    nano \
    procps \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Claude Code
RUN npm install -g @anthropic-ai/claude-code

# Install OpenCode
RUN npm install -g opencode-ai

# Install MCP servers for Slack and Gmail
RUN npm install -g @modelcontextprotocol/server-slack
RUN npm install -g @gongrzhe/server-gmail-autoauth-mcp

# Install ngrok
RUN curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
    | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
    && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
    | tee /etc/apt/sources.list.d/ngrok.list \
    && apt-get update && apt-get install -y ngrok \
    && rm -rf /var/lib/apt/lists/*

# Set up Claude Code configuration directory and copy default settings
# (MCP server configs + skills; users can override by mounting their own settings.json)
RUN mkdir -p /root/.claude
COPY settings.json /root/.claude/settings.json

# Student shell quality-of-life improvements
RUN echo 'export PS1="ai-course:\\w# "' >> /root/.bashrc && \
    echo 'alias ll="ls -alF"' >> /root/.bashrc && \
    echo 'alias la="ls -A"' >> /root/.bashrc && \
    echo 'alias l="ls -CF"' >> /root/.bashrc && \
    echo 'alias python="python3"' >> /root/.bashrc && \
    echo 'alias pip="pip3"' >> /root/.bashrc

CMD ["/bin/bash"]
