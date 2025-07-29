import random


class Pokemon:
    ventajas = {
        "Fire": ["Grass"],
        "Water": ["Fire"],
        "Grass": ["Water"],
        "Electric": ["Water"],
    }

    def __init__(self, name: str, type: str = "Normal", attack: float = 1, health: float = 10):
        if attack <= 0:
            raise ValueError("El ataque debe ser mayor que cero.")
        if health <= 0:
            raise ValueError("La salud debe ser mayor que cero.")

        self.name = name
        self.type = type
        self.attack = attack
        self.health = health

    def __str__(self):
        return f"{self.name} ({self.type}, Salud: {self.health}, Ataque: {self.attack})"

    def tiene_ventaja(self, contra_tipo):
        return contra_tipo in self.ventajas.get(self.type, [])

    def calcular_power_contra(self, otro_pokemon):
        bonus = 1.5 if self.tiene_ventaja(otro_pokemon.type) else 1
        return self.attack * bonus * self.health

    def battle(self, otro_pokemon):
        print(f"\n⚔️ {self.name} vs {otro_pokemon.name}")

        # Guardamos ataques originales por si queremos resetear después
        ataque_original_self = self.attack
        ataque_original_otro = otro_pokemon.attack

        # Posible ataque especial de self
        if random.choice([True, False]):
            bonus = random.uniform(0, 0.15)
            aumento = self.attack * bonus
            self.attack += aumento
            print(f"✨ {self.name} activa su Ataque Especial: +{round(aumento, 2)} de ataque")

        # Posible ataque especial del otro
        if random.choice([True, False]):
            bonus = random.uniform(0, 0.15)
            aumento = otro_pokemon.attack * bonus
            otro_pokemon.attack += aumento
            print(
                f"✨ {otro_pokemon.name} activa su Ataque Especial: +{round(aumento, 2)} de ataque"
            )

        # Calculamos poder con ventaja de tipo incluida
        poder_self = self.calcular_power_contra(otro_pokemon)
        poder_otro = otro_pokemon.calcular_power_contra(self)

        print(f"🧮 {self.name} - Poder total: {round(poder_self, 2)}")
        print(f"🧮 {otro_pokemon.name} - Poder total: {round(poder_otro, 2)}")

        # Resultado
        if poder_self > poder_otro:
            print(f"🏆 ¡{self.name} gana!")
            resultado = self.name
        elif poder_self < poder_otro:
            print(f"🏆 ¡{otro_pokemon.name} gana!")
            resultado = otro_pokemon.name
        else:
            print("🤝 ¡Empate!")
            resultado = "Empate"

        # (Opcional) Restaurar el ataque original
        self.attack = ataque_original_self
        otro_pokemon.attack = ataque_original_otro

        return resultado
