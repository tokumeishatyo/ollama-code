FROM python:3

ARG USERNAME=klab
ARG GROUPNAME=klab
ARG UID=1000
ARG GID=1000

#Group and USER
RUN groupadd -g $GID $GROUPNAME \
&& useradd -m -s /bin/bash -u $UID -g $GID $USERNAME \
&& apt-get update && apt-get install -y sudo git curl \
&& echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
&& chmod 0440 /etc/sudoers.d/$USERNAME 

# Pythonパッケージのインストール
RUN pip install requests

USER $USERNAME

# Ollamaクライアントのインストール
RUN curl -fsSL https://ollama.com/install.sh | sh

# Coding Agentファイルのコピー
COPY --chown=$USERNAME:$GROUPNAME ollama_code.py /home/$USERNAME/ollama_code.py
RUN chmod +x /home/$USERNAME/ollama_code.py

# Ollamaサービス起動スクリプト
COPY --chown=$USERNAME:$GROUPNAME start-ollama.sh /home/$USERNAME/start-ollama.sh
RUN chmod +x /home/$USERNAME/start-ollama.sh

WORKDIR /workspace

CMD ["/home/klab/start-ollama.sh"]