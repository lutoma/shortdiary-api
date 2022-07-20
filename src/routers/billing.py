from fastapi import APIRouter, Depends, Request, Header
from models import User, Subscription
from typing import Optional
from pydantic import BaseModel
from tortoise.exceptions import DoesNotExist
from .auth import get_current_user
from config import APIConfig
import stripe

stripe.api_key = APIConfig().stripe.api_key
router = APIRouter()


class SubscribeStatus(BaseModel):
	message: str
	session_url: Optional[str]


@router.post('/subscribe', response_model=SubscribeStatus)
async def subscribe(user: User = Depends(get_current_user)):
	print('user', user)
	if not user.stripe_id:
		try:
			stripe_customer = stripe.Customer.create(email=user.email)
		except Exception as e:
			return SubscribeStatus(message=repr(e))

		user.stripe_id = stripe_customer.id
		await user.save()

	try:
		checkout_session = stripe.checkout.Session.create(
			customer=user.stripe_id,
			line_items=[
				{
					'price': APIConfig().stripe.price,
					'quantity': 1,
				},
			],
			mode='subscription',
			success_url='http://localhost:3000/settings',
			cancel_url='http://localhost:3000/settings',
		)
	except Exception as e:
		return SubscribeStatus(message=repr(e))

	return SubscribeStatus(message='ok', session_url=checkout_session.url)


@router.post('/portal', response_model=SubscribeStatus)
async def portal(user: User = Depends(get_current_user)):
	if not user.stripe_id:
		try:
			stripe_customer = stripe.Customer.create(email=user.email)
		except Exception as e:
			return SubscribeStatus(message=repr(e))

		user.stripe_id = stripe_customer.id
		await user.save()

	try:
		portal_session = stripe.billing_portal.Session.create(customer=user.stripe_id,
			return_url='http://localhost:3000')
		print(portal_session)
		print(portal_session.url)

	except Exception as e:
		print(e)
		return SubscribeStatus(message=repr(e))

	return SubscribeStatus(message='ok', session_url=portal_session.url)


@router.post('/stripe-webhook', include_in_schema=False)
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
	data = await request.body()

	try:
		event = stripe.Webhook.construct_event(
			payload=data,
			sig_header=stripe_signature,
			secret=APIConfig().stripe.webhook_secret
		)

		event_data = event['data']['object']
	except Exception as e:
		return {'error': str(e)}

	if event['type'] not in ('customer.subscription.updated', 'customer.subscription.deleted'):
		return {"status": "success"}

	try:
		user = await User.get(stripe_id=event_data['customer'])
	except DoesNotExist:
		return {'error': 'No user with stripe id'}

	await user.fetch_related('subscription')

	if event['type'] == 'customer.subscription.updated':
		if user.subscription:
			sub = user.subscription
			sub.user = user
			sub.stripe_id = event_data['id']
			sub.status = event_data['status']
			sub.plan = 'standard'
			sub.plan_name = 'Standard subscription'
			sub = await sub.save()
		else:
			sub = await Subscription.create(
				user=user,
				stripe_id=event_data['id'],
				status=event_data['status'],
				plan='standard',
				plan_name='Standard subscription'
			)
	elif event['type'] == 'customer.subscription.deleted':
		if user.subscription:
			await user.subscription.delete()

	return {"status": "success"}
