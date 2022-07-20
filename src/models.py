from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator


class User(Model):
	id = fields.UUIDField(pk=True)
	joined = fields.DatetimeField(auto_now_add=True)
	last_seen = fields.DatetimeField(auto_now_add=True)

	email = fields.CharField(max_length=255, unique=True, index=True)
	email_verified = fields.BooleanField(default=False)

	# Salt used during derivation of ephemeral key from login password
	ephemeral_key_salt = fields.CharField(max_length=22, null=True)

	# User master key, encrypted using ephemeral key
	master_key = fields.CharField(max_length=64, null=True)

	# Nonce used during encryption of master key
	master_key_nonce = fields.CharField(max_length=32, null=True)

	# argon2id hash of password
	password = fields.CharField(max_length=100)

	# Old Django username for users that have not logged in since the migration
	legacy_username = fields.CharField(max_length=255, null=True, unique=True)

	stripe_id = fields.CharField(max_length=255, null=True, index=True)

	class PydanticMeta:
		exclude = ('password', 'legacy_username', 'joined', 'last_seen', 'stripe_id',
			'stripe_intent_id')

	def __str__(self):
		return self.email

	async def has_active_subscription(self):
		await self.fetch_related('subscription')
		if self.subscription and self.subscription.status == 'active':
			return True
		return False


User_Pydantic = pydantic_model_creator(User, name='User')
UserIn_Pydantic = pydantic_model_creator(User, name='UserIn', exclude_readonly=True)


class Post(Model):
	id = fields.UUIDField(pk=True)
	author = fields.ForeignKeyField('models.User', related_name='posts',
		on_delete=fields.CASCADE, index=True)

	date = fields.DateField()
	last_changed = fields.DatetimeField(auto_now=True)
	created = fields.DatetimeField(auto_now_add=True)

	# Encryption format used by this post. 0 = unencrypted (legacy posts from
	# before client-side encryption used to exist and use has not converted
	# yet), 1 = current format, all other values reserved for future use
	format_version = fields.IntField(default=1)

	# Nonce used for post encryption
	nonce = fields.CharField(max_length=32, null=True)
	data = fields.BinaryField()

	class Meta:
		unique_together = (('author', 'date'), )

	class PydanticMeta:
		exclude = ('author')

	def __str__(self):
		return self.name


Post_Pydantic = pydantic_model_creator(Post, name='Post')
PostIn_Pydantic = pydantic_model_creator(Post, name='PostIn', exclude_readonly=True)


class Subscription(Model):
	id = fields.UUIDField(pk=True)
	user = fields.OneToOneField('models.User', related_name='subscription',
		on_delete=fields.CASCADE, index=True)

	stripe_id = fields.CharField(max_length=255, null=True, index=True)
	status = fields.CharField(max_length=255)

	plan = fields.CharField(max_length=100)
	plan_name = fields.CharField(max_length=500)

	last_changed = fields.DatetimeField(auto_now=True)
	start_time = fields.DatetimeField(auto_now_add=True)
	end_time = fields.DatetimeField(null=True)

	class PydanticMeta:
		exclude = ('user', 'stripe_id', 'last_changed')

	def __str__(self):
		return f'Subscription {self.id} ({self.status}) [{self.stripe_id}]'


Subscription_Pydantic = pydantic_model_creator(Subscription, name='Subscription')
