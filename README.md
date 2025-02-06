# Build-and-sign

The build-and-sign process includes Konflux CI pipelines, Github actions, and Python scripts that verify new kernel versions and driver versions from specified sources.

These scripts trigger the Konflux pipelines for those kernel modules to be built and then signed using the AWS KMS service, followed by uploading them to a configured private repository.
