import argparse
import json

def get_mock_population_data(postal_code):
    # Génération de données fictives (mock) réalistes
    # Dans une version future, ceci sera remplacé par un appel à l'API de l'INSEE.
    return {
        "postal_code": postal_code,
        "population_total": 35420,
        "seniors_percentage": 22.4,
        "overcrowding_percentage": 4.1
    }

def main():
    parser = argparse.ArgumentParser(description="Skill Vulnérabilité Population")
    parser.add_argument("--args", required=True, help="Le code postal de la zone recherchée")
    args = parser.parse_args()

    # Extraction du code postal (on assume que l'argument passé est le code postal)
    postal_code = args.args.strip()

    # Récupération des données
    data = get_mock_population_data(postal_code)

    # Renvoi du JSON propre sur la sortie standard
    print(json.dumps(data))

if __name__ == "__main__":
    main()
