from globus_ssh.config import Config
from globus_ssh.token  import Token
import tempfile
import random
import string
import stat
import os

def _create_temp_file():
    return tempfile.NamedTemporaryFile()

def _create_random_string(length):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

class TestConfig():
    #temp_file=None
    umask_value=None

    @classmethod
    def setup_class(cls):
        cls.umask_value = os.umask(0)
        os.umask(cls.umask_value)
 
    @classmethod
    def teardown_class(cls):
        os.umask(cls.umask_value)
        cls.umask_value = None

    def test_no_such_file(self):
        # saving only the name deletes the file before use
        temp_file_name = _create_temp_file().name
        assert Config(temp_file_name)

    def test_load_missing_token(self):
        section = _create_random_string(6)
        temp_file = _create_temp_file()
        assert (Config(temp_file.name).load_token(section) == None)

    def test_store_load_token_str(self):
        section = _create_random_string(6)
        key='scope'
        value="XXX"
        temp_file = _create_temp_file()
        Config(temp_file.name).save_token(section, Token(**{key:value}))
        assert (Config(temp_file.name).load_token(section) == Token(**{key:value}))

    def test_store_load_token_int(self):
        section = _create_random_string(6)
        key='expires_at_seconds'
        value=12
        temp_file = _create_temp_file()
        Config(temp_file.name).save_token(section, Token(**{key:value}))
        assert (Config(temp_file.name).load_token(section) == Token(**{key:value}))

    def test_delete_token(self):
        section = _create_random_string(6)
        key     = 'scope'
        value   = "XXX"
        Config(_create_temp_file().name).save_token(section, Token(**{key:value}))
        Config(_create_temp_file().name).delete_token(section)
        assert (Config(_create_temp_file().name).load_token(section) == None)

    def test_preserve_umask(self):
        section   = _create_random_string(6)
        key       = 'scope'
        value     = "XXX"
        temp_file = _create_temp_file()

        # Initialize a wide umask
        initial_mask = os.umask(0)
        Config(temp_file.name).save_token(section, Token(**{key:value}))
        assert oct(os.umask(initial_mask)) == oct(0)

        # Initialize an unusual umask
        os.umask(127)
        Config(temp_file.name).save_token(section, Token(**{key:value}))
        assert oct(os.umask(initial_mask)) == oct(127)

    def test_permissions(self):
        section      = _create_random_string(6)
        key          = 'scope'
        value        = "XXX"
        temp_file    = _create_temp_file()
        initial_mask = os.umask(0)

        perms = stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO

        # Test config file permissions for save_token()
        os.chmod(temp_file.name, perms)
        assert os.stat(temp_file.name).st_mode&perms == perms
        Config(temp_file.name).save_token(section, Token(**{key:value}))
        assert os.stat(temp_file.name).st_mode&perms == stat.S_IRUSR|stat.S_IWUSR

        # Test config file permissions for delete_token()
        os.chmod(temp_file.name, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)
        assert os.stat(temp_file.name).st_mode&perms == perms
        Config(temp_file.name).delete_token(section)
        assert os.stat(temp_file.name).st_mode&perms == stat.S_IRUSR|stat.S_IWUSR

        # Reset our umask
        os.umask(initial_mask)

