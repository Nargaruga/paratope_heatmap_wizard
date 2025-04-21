FROM continuumio/miniconda3

RUN conda install -c conda-forge biopython -y
RUN conda install -c bioconda hmmer=3.3.2 -y

RUN apt update && apt install -y dos2unix wget build-essential

COPY . /ANARCI
WORKDIR /ANARCI
RUN pip install -r requirements.txt
RUN find . -type f -print0 | xargs -0 dos2unix

RUN mkdir /muscle_dir
WORKDIR /muscle_dir
RUN wget https://www.drive5.com/muscle/muscle_src_3.8.1551.tar.gz
RUN tar -xzvf muscle_src_3.8.1551.tar.gz
RUN make
RUN cp muscle /ANARCI/bin
RUN rm -rf /muscle_dir

WORKDIR /ANARCI
RUN python setup.py install

ENTRYPOINT ["ANARCI"]
