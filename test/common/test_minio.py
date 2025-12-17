from dspider.common.minio_service import minio_client

def test_minio_client():
    assert minio_client is not None

if __name__ == '__main__':
    test_minio_client()
