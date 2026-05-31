# Use the official AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.12

# Install system dependencies needed for building native extensions (like chroma-hnswlib)
RUN dnf install -y \
    gcc-c++ \
    && dnf clean all

# Copy the requirements file into the container
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the application dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code into the container
COPY . ${LAMBDA_TASK_ROOT}

# Set the CMD to your mangum handler
CMD ["local_server.handler"]
