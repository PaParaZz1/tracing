import setuptools


setuptools.setup(
    name='petrel-tracing',
    version='0.0.1',
    packages=setuptools.find_packages(),
    install_requires=['jaeger-client', 'opentracing', 'grpcio-opentracing'],
    python_requires='>=3.6',
    zip_safe=False,
)
