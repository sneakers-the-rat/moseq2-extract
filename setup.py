from setuptools import setup

setup(
    name='moseq2',
    author='Jeff Markowitz',
    description='To boldly go where no mouse has gone before',
    version='0.01a',
    platforms=['mac', 'unix'],
    install_requires=['h5py', 'matplotlib', 'scipy>=0.19',
                      'scikit-image==0.13', 'scikit-learn==0.19',
                      'tqdm', 'statsmodels==0.8.0',
                      'numpy==1.13.1', 'joblib==0.11', 'opencv-python',
                      'click'],
    python_requires='>=3.4',
    entry_points={'console_scripts': ['moseq2 = moseq2.cli:cli']}
)
