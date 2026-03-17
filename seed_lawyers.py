from database import db, user_model

def seed_lawyers():
    lawyers = [
        {
            "name": "Arjun Sharma",
            "email": "arjun.sharma@lexai.in",
            "phone": "9812345670",
            "experience": "Senior Criminal Defense Advocate with 15+ years of experience. Won several high-profile bail applications and trial court cases."
        },
        {
            "name": "Priya Iyer",
            "email": "priya.iyer@legalpro.com",
            "phone": "9812345671",
            "experience": "Specialist in Family Law and Divorce mediation. 10 years of experience in high court litigation and out-of-court settlements."
        },
        {
            "name": "Vikram Singh",
            "email": "vikram.singh@singhlegal.co",
            "phone": "9812345672",
            "experience": "Expert in Corporate and Intellectual Property Law. Advisor to several Fortune 500 companies in India on patent compliance."
        },
        {
            "name": "Meera Reddy",
            "email": "meera.reddy@lexlaw.com",
            "phone": "9812345673",
            "experience": "Land and Property Dispute expert. Handled over 200 real estate recovery and verification cases."
        },
        {
            "name": "Rohan Deshmukh",
            "email": "rohan.d@mahalegal.in",
            "phone": "9812345674",
            "experience": "Public Interest Litigation (PIL) specialist. 8 years of experience fighting for environmental and civil rights in Mumbai."
        },
        {
            "name": "Sanya Malhotra",
            "email": "sanya.m@malhotralegal.in",
            "phone": "9812345675",
            "experience": "Cyber Crime and Digital Privacy expert. Former consultant for state police units on data breach investigations."
        },
        {
            "name": "Aditya Verma",
            "email": "aditya.v@vermalaw.co",
            "phone": "9812345676",
            "experience": "Consumer Disputes and Labor Law specialist. Dedicated to helping citizens fight against unfair trade practices."
        },
        {
            "name": "Ananya Gupta",
            "email": "ananya.g@guptalegal.com",
            "phone": "9812345677",
            "experience": "Tax and Financial Regulatory lawyer. Expertise in GST disputes and corporate tax planning for 12 years."
        },
        {
            "name": "Kabir Khan",
            "email": "kabir.k@khanassociates.in",
            "phone": "9812345678",
            "experience": "Human Rights and Constitutional Law advocate. Represented marginalized communities in several landmark cases."
        },
        {
            "name": "Neha Joshi",
            "email": "neha.j@joshilegal.co",
            "phone": "9812345679",
            "experience": "Maritime and International Trade Law specialist. Consultant for port authorities and multi-national logistics firms."
        }
    ]

    password = "LawyerPassword123!"

    print("Seeding 10 lawyers into the database...")

    for i, l in enumerate(lawyers):
        # Generate some mock private data
        lawyer_data = {
            "aadhar": f"{1000 + i}-{2000 + i}-{3000 + i}-{4000 + i}",
            "father_name": f"Mr. {l['name'].split()[-1]} Senior",
            "mother_name": f"Mrs. {l['name'].split()[-1]}",
            "lawyer_id": f"BC/{100 + i}/{2010 + i}",
            "experience_summary": l['experience']
        }

        # Check if exists
        if user_model.find_by_email(l['email']):
            print(f"Skipping {l['email']} (already exists)")
            continue

        user_model.create_user(
            name=l['name'],
            email=l['email'],
            phone=l['phone'],
            password=password,
            role='lawyer',
            lawyer_data=lawyer_data
        )
        print(f"Successfully added {l['name']}")

    print("\n--- Seeding Complete ---")
    print(f"All lawyers share the password: {password}")

if __name__ == "__main__":
    seed_lawyers()
