import os
import unittest
from datetime import date, time, timedelta
from decimal import Decimal


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-only-secret"


from app import create_app
from app.extensions import db
from app.models import (
    Address,
    Booking,
    CustomerProfile,
    ProviderAvailability,
    ProviderProfile,
    ProviderService,
    Service,
    ServiceCategory,
    User,
)


class PlatformWorkflowTests(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
        )

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def create_user(self, name, email, role):
        user = User(
            name=name,
            email=email,
            role=role
        )
        user.set_password("Password123!")
        db.session.add(user)
        db.session.flush()
        return user

    def login(self, client, email):
        response = client.post(
            "/auth/login",
            data={
                "email": email,
                "password": "Password123!"
            }
        )
        self.assertEqual(response.status_code, 302)

    def seed_marketplace(self):
        customer = self.create_user(
            "Customer",
            "customer@test.example",
            "CUSTOMER"
        )
        provider_user = self.create_user(
            "Provider",
            "provider@test.example",
            "PROVIDER"
        )
        admin = self.create_user(
            "Admin",
            "admin@test.example",
            "ADMIN"
        )

        category = ServiceCategory(
            name="Yoga",
            slug="yoga",
            is_active=True
        )
        db.session.add(category)
        db.session.flush()

        service = Service(
            category_id=category.id,
            name="Home Yoga",
            slug="home-yoga",
            duration_minutes=60,
            base_price=Decimal("500.00"),
            service_mode="HOME",
            is_active=True
        )
        db.session.add(service)
        db.session.flush()

        provider = ProviderProfile(
            user_id=provider_user.id,
            qualification="Certified",
            specialization="Yoga",
            service_city="Delhi",
            verification_status="APPROVED",
            is_available=True
        )
        db.session.add(provider)
        db.session.flush()

        provider_service = ProviderService(
            provider_id=provider.id,
            service_id=service.id,
            price=Decimal("450.00"),
            duration_minutes=60,
            is_active=True
        )
        db.session.add(provider_service)

        booking_date = date.today() + timedelta(days=7)
        slot = ProviderAvailability(
            provider_id=provider.id,
            day_of_week=booking_date.weekday(),
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True
        )
        db.session.add(slot)

        address = Address(
            user_id=customer.id,
            label="Home",
            address_line_1="1 Test Street",
            locality="Test Locality",
            city="Delhi",
            state="Delhi",
            postal_code="110001",
            is_default=True
        )
        db.session.add(address)
        db.session.commit()

        return {
            "customer_id": customer.id,
            "provider_user_id": provider_user.id,
            "admin_id": admin.id,
            "category_id": category.id,
            "service_id": service.id,
            "provider_id": provider.id,
            "provider_service_id": provider_service.id,
            "slot_id": slot.id,
            "address_id": address.id,
            "booking_date": booking_date,
        }

    def test_all_get_routes_render_for_their_roles(self):
        with self.app.app_context():
            data = self.seed_marketplace()

        guest_client = self.app.test_client()
        guest_paths = [
            "/",
            "/auth/login",
            "/auth/register",
            "/services/",
            "/services/category/yoga",
            "/services/home-yoga",
        ]

        for path in guest_paths:
            with self.subTest(role="guest", path=path):
                self.assertEqual(
                    guest_client.get(path).status_code,
                    200
                )

        customer_client = self.app.test_client()
        self.login(customer_client, "customer@test.example")
        customer_paths = [
            "/customer/profile",
            "/customer/addresses/add",
            f"/customer/addresses/{data['address_id']}/edit",
            "/bookings/history",
            f"/bookings/new/{data['service_id']}",
        ]

        for path in customer_paths:
            with self.subTest(role="customer", path=path):
                self.assertEqual(
                    customer_client.get(path).status_code,
                    200
                )

        provider_client = self.app.test_client()
        self.login(provider_client, "provider@test.example")
        provider_paths = [
            "/provider/",
            "/provider/profile",
            "/provider/services",
            "/provider/services/add",
            f"/provider/services/{data['provider_service_id']}/edit",
            "/provider/availability",
            "/provider/availability/add",
            f"/provider/availability/{data['slot_id']}/edit",
            "/bookings/provider",
        ]

        for path in provider_paths:
            with self.subTest(role="provider", path=path):
                self.assertEqual(
                    provider_client.get(path).status_code,
                    200
                )

        admin_client = self.app.test_client()
        self.login(admin_client, "admin@test.example")
        admin_paths = [
            "/admin/",
            "/admin/categories",
            "/admin/categories/add",
            f"/admin/categories/{data['category_id']}/edit",
            "/admin/services",
            "/admin/services/add",
            f"/admin/services/{data['service_id']}/edit",
            "/admin/providers",
            "/admin/provider-candidates",
            "/admin/bookings",
        ]

        for path in admin_paths:
            with self.subTest(role="admin", path=path):
                self.assertEqual(
                    admin_client.get(path).status_code,
                    200
                )

    def test_registration_creates_customer_profile_and_hashes_password(self):
        client = self.app.test_client()

        response = client.post(
            "/auth/register",
            data={
                "name": "New Customer",
                "email": "new.customer@test.example",
                "phone": "9876543210",
                "password": "Password123!",
                "confirm_password": "Password123!",
            }
        )

        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            user = db.session.execute(
                db.select(User).where(
                    User.email == "new.customer@test.example"
                )
            ).scalar_one()

            self.assertNotEqual(
                user.password_hash,
                "Password123!"
            )
            self.assertIsNotNone(user.customer_profile)

    def test_customer_routes_reject_provider_role(self):
        with self.app.app_context():
            provider = self.create_user(
                "Provider",
                "provider@test.example",
                "PROVIDER"
            )
            db.session.commit()

        client = self.app.test_client()
        self.login(client, "provider@test.example")

        self.assertEqual(
            client.get("/customer/profile").status_code,
            403
        )
        self.assertEqual(
            client.get("/customer/addresses/add").status_code,
            403
        )

    def test_admin_add_service_form_renders(self):
        with self.app.app_context():
            self.create_user(
                "Admin",
                "admin@test.example",
                "ADMIN"
            )
            db.session.add(
                ServiceCategory(
                    name="Yoga",
                    slug="yoga",
                    is_active=True
                )
            )
            db.session.commit()

        client = self.app.test_client()
        self.login(client, "admin@test.example")

        response = client.get("/admin/services/add")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Create Service", response.data)

    def test_provider_can_go_online_after_configuration(self):
        with self.app.app_context():
            data = self.seed_marketplace()
            provider = db.session.get(
                ProviderProfile,
                data["provider_id"]
            )
            provider.is_available = False
            db.session.commit()

        client = self.app.test_client()
        self.login(client, "provider@test.example")

        response = client.post(
            "/provider/availability-status/toggle"
        )

        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            provider = db.session.get(
                ProviderProfile,
                data["provider_id"]
            )
            self.assertTrue(provider.is_available)

    def test_booking_creation_conflict_and_status_lifecycle(self):
        with self.app.app_context():
            data = self.seed_marketplace()

        customer_client = self.app.test_client()
        self.login(customer_client, "customer@test.example")

        booking_data = {
            "provider_service_id": str(
                data["provider_service_id"]
            ),
            "booking_date": data["booking_date"].isoformat(),
            "start_time": "10:00",
            "address_id": str(data["address_id"]),
            "customer_notes": "Test booking",
        }

        response = customer_client.post(
            f"/bookings/new/{data['service_id']}",
            data=booking_data
        )
        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            booking = db.session.execute(
                db.select(Booking)
            ).scalar_one()
            booking_id = booking.id
            self.assertEqual(booking.status, "PENDING")

        conflicting_data = dict(booking_data)
        conflicting_data["start_time"] = "10:30"
        customer_client.post(
            f"/bookings/new/{data['service_id']}",
            data=conflicting_data
        )

        with self.app.app_context():
            count = db.session.scalar(
                db.select(db.func.count()).select_from(Booking)
            )
            self.assertEqual(count, 1)

        provider_client = self.app.test_client()
        self.login(provider_client, "provider@test.example")

        self.assertEqual(
            provider_client.get("/bookings/provider").status_code,
            200
        )

        response = provider_client.post(
            f"/bookings/provider/{booking_id}/status",
            data={"action": "CONFIRM"}
        )
        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            self.assertEqual(
                db.session.get(Booking, booking_id).status,
                "CONFIRMED"
            )

        response = provider_client.post(
            f"/bookings/provider/{booking_id}/status",
            data={"action": "COMPLETE"}
        )
        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            self.assertEqual(
                db.session.get(Booking, booking_id).status,
                "COMPLETED"
            )

        admin_client = self.app.test_client()
        self.login(admin_client, "admin@test.example")

        self.assertEqual(
            admin_client.get("/admin/bookings").status_code,
            200
        )
        response = admin_client.post(
            f"/admin/bookings/{booking_id}/status",
            data={"status": "CONFIRMED"}
        )
        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            self.assertEqual(
                db.session.get(Booking, booking_id).status,
                "CONFIRMED"
            )

        response = customer_client.post(
            f"/bookings/{booking_id}/cancel"
        )
        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            self.assertEqual(
                db.session.get(Booking, booking_id).status,
                "CANCELLED"
            )


if __name__ == "__main__":
    unittest.main()
