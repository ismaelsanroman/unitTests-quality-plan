import secrets


class AtaqueInvalidoError(ValueError):
    """Excepción lanzada cuando el ataque es inválido."""

    def __str__(self) -> str:
        """Devuelve el mensaje de error para ataque inválido."""
        return "Attack value must be greater than zero."


class SaludInvalidaError(ValueError):
    """Excepción lanzada cuando la salud es inválida."""

    def __str__(self) -> str:
        """Devuelve el mensaje de error para salud inválida."""
        return "Health value must be greater than zero."


class Pokemon:
    """Clase que representa un Pokémon con tipo, salud y ataque."""

    ventajas: dict[str, list[str]] = {
        "Fire": ["Grass"],
        "Water": ["Fire"],
        "Grass": ["Water"],
        "Electric": ["Water"],
    }

    def __init__(
        self,
        name: str,
        tipo: str = "Normal",
        attack: float = 1,
        health: float = 10,
    ) -> None:
        """
        Inicializa un nuevo Pokémon.

        Args:
            name: Nombre del Pokémon.
            tipo: Tipo elemental.
            attack: Poder de ataque.
            health: Salud.
        """
        if attack <= 0:
            raise AtaqueInvalidoError()
        if health <= 0:
            raise SaludInvalidaError()
        self.name: str = name
        self.tipo: str = tipo
        self.attack: float = attack
        self.health: float = health

    def __str__(self) -> str:
        """Devuelve una representación en texto del Pokémon."""
        return f"{self.name} ({self.tipo}, Salud: {self.health}, Ataque: {self.attack})"

    def tiene_ventaja(self, contra_tipo: str) -> bool:
        """
        Indica si este Pokémon tiene ventaja de tipo sobre otro.

        Args:
            contra_tipo: Tipo del Pokémon rival.

        Returns
        -------
            True si tiene ventaja, False en caso contrario.
        """
        return contra_tipo in self.ventajas.get(self.tipo, [])

    def calcular_power_contra(self, otro_pokemon: "Pokemon") -> float:
        """
        Calcula el poder contra otro Pokémon teniendo en cuenta la ventaja de tipo.

        Args:
            otro_pokemon: El Pokémon rival.

        Returns
        -------
            Poder total frente al rival.
        """
        bonus: float = 1.5 if self.tiene_ventaja(otro_pokemon.tipo) else 1.0
        return self.attack * bonus * self.health

    def battle(self, otro_pokemon: "Pokemon") -> str:
        """
        Simula un combate entre dos Pokémon y devuelve el nombre del ganador o 'Empate'.

        Args:
            otro_pokemon: El Pokémon rival.

        Returns
        -------
            Nombre del ganador o 'Empate'.
        """
        ataque_original_self: float = self.attack
        ataque_original_otro: float = otro_pokemon.attack

        # Ataque especial aleatorio (más seguro con secrets)
        if secrets.choice([True, False]):
            bonus = secrets.randbelow(15) / 100
            self.attack += self.attack * bonus

        if secrets.choice([True, False]):
            bonus = secrets.randbelow(15) / 100
            otro_pokemon.attack += otro_pokemon.attack * bonus

        poder_self: float = self.calcular_power_contra(otro_pokemon)
        poder_otro: float = otro_pokemon.calcular_power_contra(self)

        if poder_self > poder_otro:
            resultado: str = self.name
        elif poder_self < poder_otro:
            resultado = otro_pokemon.name
        else:
            resultado = "Draw"

        # Restaurar ataques originales
        self.attack = ataque_original_self
        otro_pokemon.attack = ataque_original_otro

        return resultado
