
import os, sys
os.chdir(r"C:\Users\s.kramorov\PycharmProjects\djangoProject1")
sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoProject1.settings")
import django; django.setup()

from storage_manager.storage_backends.cloudru import CloudRuStorage

cloud = CloudRuStorage()
TEST_KEY = "_test_acl_check.txt"

print("=" * 50)
print("АДМИНСКИЙ АККАУНТ")
print("=" * 50)

# Upload
print("\n1. Upload:")
try:
    cloud._save(TEST_KEY, __import__("io").BytesIO(b"admin upload test"))
    print("   OK")
except Exception as e:
    print(f"   FAIL: {e}")

# Exists
print("\n2. Exists:")
try:
    ok = cloud.exists(TEST_KEY)
    print(f"   {'OK' if ok else 'FAIL'}")
except Exception as e:
    print(f"   FAIL: {e}")

# Open (admin uses reader client for _open)
print("\n3. Open (читает через reader):")
try:
    f = cloud._open(TEST_KEY, 'rb')
    print(f"   OK: {f.read()}")
    f.close()
except Exception as e:
    print(f"   FAIL: {e}")

print("\n" + "=" * 50)
print("ЧИТАТЕЛЬСКИЙ АККАУНТ (отдельный клиент)")
print("=" * 50)

# Try to read via reader
print("\n4. Reader: exists:")
try:
    ok = cloud.s3_reader.head_object(Bucket=cloud.bucket_name, Key=TEST_KEY)
    print(f"   OK")
except Exception as e:
    print(f"   FAIL: {e}")

print("\n5. Reader: get_object:")
try:
    resp = cloud.s3_reader.get_object(Bucket=cloud.bucket_name, Key=TEST_KEY)
    print(f"   OK: {resp['Body'].read()}")
except Exception as e:
    print(f"   FAIL: {e}")

print("\n6. Reader: delete_object (должен УПАСТЬ):")
try:
    cloud.s3_reader.delete_object(Bucket=cloud.bucket_name, Key=TEST_KEY)
    print("   FAIL — удалил! (не должно быть прав)")
except Exception as e:
    err = str(e)[:150]
    print(f"   OK — ожидаемо: {err}")

print("\n7. Reader: put_object (должен УПАСТЬ):")
try:
    cloud.s3_reader.put_object(
        Bucket=cloud.bucket_name,
        Key="_test_reader_upload.txt",
        Body=b"should fail",
    )
    print("   FAIL — залил! (не должно быть прав)")
    # Clean up via admin
    cloud.s3_admin.delete_object(Bucket=cloud.bucket_name, Key="_test_reader_upload.txt")
except Exception as e:
    err = str(e)[:150]
    print(f"   OK — ожидаемо: {err}")

# Cleanup via admin
print("\n8. Admin: delete_object (очистка):")
try:
    cloud.s3_admin.delete_object(Bucket=cloud.bucket_name, Key=TEST_KEY)
    print("   OK")
except Exception as e:
    print(f"   FAIL: {e}")

print("\n" + "=" * 50)
print("ТЕСТЫ ЗАВЕРШЕНЫ")
print("=" * 50)
