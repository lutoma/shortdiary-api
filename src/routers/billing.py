from fastapi import APIRouter, Depends, Request, Header, HTTPException
from models import User, Subscription
from pydantic import BaseModel
from tortoise.exceptions import DoesNotExist
from .auth import get_current_user
from config import APIConfig
import stripe

stripe.api_key = APIConfig().stripe.api_key
router = APIRouter()


class StripeRedirectResponse(BaseModel):
	session_url: str


async def get_stripe_id(user):
	if not user.stripe_id:
		try:
			stripe_customer = stripe.Customer.create(email=user.email)
		except Exception:
			raise HTTPException(status_code=500, detail='Stripe request failed')

		user.stripe_id = stripe_customer.id
		await user.save()

	return user.stripe_id


@router.post('/subscribe', response_model=StripeRedirectResponse)
async def subscribe(user: User = Depends(get_current_user)):
	await user.fetch_related('subscription')
	if all((user.subscription, user.subscription.status == 'active',
		user.subscription.plan != 'earlyadopter')):

		raise HTTPException(status_code=422, detail='User already has an active subscription')

	stripe_id = await get_stripe_id(user)

	try:
		checkout_session = stripe.checkout.Session.create(
			customer=stripe_id,
			line_items=[
				{
					'price': APIConfig().stripe.price,
					'quantity': 1,
				},
			],
			mode='subscription',
			success_url=f'{APIConfig().frontend_url}/settings/billing',
			cancel_url=f'{APIConfig().frontend_url}/settings/billing',
		)
	except Exception:
		raise HTTPException(status_code=500, detail='Stripe request failed')

	return StripeRedirectResponse(session_url=checkout_session.url)


@router.post('/portal', response_model=StripeRedirectResponse)
async def portal(user: User = Depends(get_current_user)):
	stripe_id = await get_stripe_id(user)

	try:
		portal_session = stripe.billing_portal.Session.create(customer=stripe_id,
			return_url=f'{APIConfig().frontend_url}/settings/billing')
	except Exception:
		raise HTTPException(status_code=500, detail='Stripe request failed')

	return StripeRedirectResponse(session_url=portal_session.url)


@router.post('/stripe-webhook', include_in_schema=False)
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
	data = await request.body()

	try:
		event = stripe.Webhook.construct_event(payload=data, sig_header=stripe_signature,
			secret=APIConfig().stripe.webhook_secret)

		event_data = event['data']['object']
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))

	if event['type'] not in ('customer.subscription.updated', 'customer.subscription.deleted'):
		raise HTTPException(status_code=422,
			detail='Unhandled event type')

	try:
		user = await User.get(stripe_id=event_data['customer'])
	except DoesNotExist:
		raise HTTPException(status_code=404, detail='No user with this stripe id')

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

	return {'status': 'success'}
