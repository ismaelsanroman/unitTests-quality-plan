import random

import pytest

from pokemon import Pokemon


@pytest.fixture
def pokemon_ejemplo():
    return {
        "pikachu": Pokemon("Pikachu", "Electric", 55, 35),
        "squirtle": Pokemon("Squirtle", "Water", 48, 44),
        "charmander": Pokemon("Charmander", "Fire", 52, 39),
        "bulbasaur": Pokemon("Bulbasaur", "Grass", 49, 45),
        "jigglypuff": Pokemon("Jigglypuff", attack=15, health=115),
        "mew": Pokemon("Mew", attack=100, health=100),
    }


@pytest.mark.pokemon
@pytest.mark.create
@pytest.mark.happy_path
def test_crear_pokemon():
    raichu = Pokemon("Raichu", "Electric", 65, 45)
    assert raichu.name == "Raichu"
    assert raichu.type == "Electric"
    assert raichu.attack == 65
    assert raichu.health == 45


@pytest.mark.pokemon
@pytest.mark.create
@pytest.mark.unhappy_path
@pytest.mark.parametrize(
    "name, attack, health, expected_message",
    [
        ("pokeprueba1", 0, 100, "ataque.*mayor que cero"),
        ("pokeprueba2", 10, 0, "salud.*mayor que cero"),
    ],
)
def test_crear_pokemon_parametrizado(name, attack, health, expected_message):
    with pytest.raises(ValueError, match=expected_message):
        Pokemon(name, attack=attack, health=health)


@pytest.mark.pokemon
@pytest.mark.battle
@pytest.mark.parametrize(
    "atacante, oponente, ganador",
    [
        ("pikachu", "squirtle", "Pikachu"),
        ("charmander", "mew", "mew"),
        ("bulbasaur", "bulbasaur", "Empate"),
    ],
)
def test_pelea_pokemon(pokemon_ejemplo, atacante, oponente, ganador):
    ganador = pokemon_ejemplo[atacante].battle(pokemon_ejemplo[oponente])
    assert ganador == ganador

    random.seed(42)
    ganador = pokemon_ejemplo[atacante].battle(pokemon_ejemplo[oponente])
    assert ganador == ganador


@pytest.mark.pokemon
@pytest.mark.create
@pytest.mark.happy_path
def test_mostrar_pokemon(pokemon_ejemplo):
    print(pokemon_ejemplo["squirtle"])
