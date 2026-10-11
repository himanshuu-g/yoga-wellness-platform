from app import create_app
from app.extensions import db
from app.models.service_category import ServiceCategory
from app.models.service import Service


app = create_app()


with app.app_context():

    # ---------------------------------------------
    # Avoid duplicate seeding
    # ---------------------------------------------
    existing_category = db.session.execute(
        db.select(ServiceCategory)
    ).scalars().first()


    if existing_category:

        print(
            "Service categories already exist. "
            "Skipping seed."
        )

    else:

        # =========================================
        # YOGA
        # =========================================

        yoga = ServiceCategory(
            name="Yoga",
            slug="yoga",
            description=(
                "Personal and specialized yoga "
                "programs for different wellness goals."
            ),
            display_order=1
        )


        # =========================================
        # HYDROTHERAPY
        # =========================================

        hydrotherapy = ServiceCategory(
            name="Hydrotherapy",
            slug="hydrotherapy",
            description=(
                "Water-based naturopathy and "
                "wellness services."
            ),
            display_order=2
        )


        # =========================================
        # MUD THERAPY
        # =========================================

        mud_therapy = ServiceCategory(
            name="Mud Therapy",
            slug="mud-therapy",
            description=(
                "Traditional naturopathy services "
                "using therapeutic mud applications."
            ),
            display_order=3
        )


        # =========================================
        # MASSAGE
        # =========================================

        massage = ServiceCategory(
            name="Massage Therapy",
            slug="massage-therapy",
            description=(
                "Wellness massage services provided "
                "by trained professionals."
            ),
            display_order=4
        )


        # =========================================
        # DIET
        # =========================================

        diet = ServiceCategory(
            name="Diet & Nutrition",
            slug="diet-nutrition",
            description=(
                "Personalized diet and nutrition "
                "consultation services."
            ),
            display_order=5
        )


        db.session.add_all([
            yoga,
            hydrotherapy,
            mud_therapy,
            massage,
            diet
        ])


        # Flush gives categories their IDs
        # before creating services.
        db.session.flush()


        # =========================================
        # SAMPLE SERVICES
        # =========================================

        services = [

            Service(
                category_id=yoga.id,
                name="One-to-One Home Yoga",
                slug="one-to-one-home-yoga",
                short_description=(
                    "Private yoga sessions at your home."
                ),
                duration_minutes=60,
                service_mode="HOME",
                display_order=1
            ),

            Service(
                category_id=yoga.id,
                name="Couples Yoga",
                slug="couples-yoga",
                short_description=(
                    "Personal yoga sessions designed "
                    "for two participants."
                ),
                duration_minutes=60,
                service_mode="HOME",
                display_order=2
            ),

            Service(
                category_id=yoga.id,
                name="Monthly Personal Yoga Program",
                slug="monthly-personal-yoga",
                short_description=(
                    "A recurring personal yoga program "
                    "with scheduled home sessions."
                ),
                duration_minutes=60,
                service_mode="HOME",
                display_order=3
            ),

            Service(
                category_id=diet.id,
                name="Diet Consultation",
                slug="diet-consultation",
                short_description=(
                    "Personal diet and nutrition consultation."
                ),
                duration_minutes=45,
                service_mode="HOME",
                display_order=1
            )

        ]


        db.session.add_all(services)

        db.session.commit()


        print(
            "Service catalog seeded successfully."
        )