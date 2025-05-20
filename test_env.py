from faker import Faker
fake = Faker()

print("Sample article:", fake.paragraph(nb_sentences=5))