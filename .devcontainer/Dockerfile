FROM almalinux:latest

# അത്യാവശ്യമായ പാക്കേജുകളും OpenSSH സെർവറും ഇൻസ്റ്റാൾ ചെയ്യുന്നു
RUN dnf update -y && dnf install -y \
    git \
    curl \
    gcc-c++ \
    make \
    sudo \
    openssh-server \
    && dnf clean all

# SSH-ന് ആവശ്യമായ ഹോസ്റ്റ് കീകൾ നിർമ്മിക്കുന്നു
RUN ssh-keygen -A && \
    mkdir -p /var/run/sshd

# 1. സൂപ്പർ യൂസർ (hacker) - മുഴുവൻ sudo പവറോടെ
RUN useradd -m -s /bin/bash kannan && \
    echo 'kannan:hacker123' | chpasswd && \
    usermod -aG wheel hacker && \
    echo "kannan ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# 2. സാധാരണ യൂസർ (guest) - sudo പവർ തീരെ ഇല്ലാത്തയാൾ
RUN useradd -m -s /bin/bash linux && \
    echo 'linux:guest123' | chpasswd

USER kannan 
WORKDIR /home/kannan 
