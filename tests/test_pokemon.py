import random

import pytest

from pokemon import AtaqueInvalidoError, Pokemon, SaludInvalidaError


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
    assert raichu.tipo == "Electric"
    assert raichu.attack == 65
    assert raichu.health == 45


@pytest.mark.pokemon
@pytest.mark.create
@pytest.mark.unhappy_path
@pytest.mark.parametrize(
    ("name", "attack", "health", "expected_message"),
    [
        ("pokeprueba1", 0, 100, "Attack.*must be greater than zero"),
        ("pokeprueba1_neg", -1, 100, "Attack.*must be greater than zero"),
        ("pokeprueba2", 10, 0, "Health.*must be greater than zero"),
        ("pokeprueba2_neg", 10, -5, "Health.*must be greater than zero"),
    ],
)
def test_crear_pokemon_parametrizado(name, attack, health, expected_message):
    with pytest.raises(ValueError, match=expected_message):
        Pokemon(name, attack=attack, health=health)


@pytest.mark.pokemon
@pytest.mark.create
def test_constructor_valores_defecto():
    magikarp = Pokemon("Magikarp")
    assert magikarp.name == "Magikarp"
    assert magikarp.tipo == "Normal"
    assert magikarp.attack == 1
    assert magikarp.health == 10


@pytest.mark.pokemon
@pytest.mark.battle
@pytest.mark.parametrize(
    ("atacante", "oponente", "ganador"),
    [
        ("pikachu", "squirtle", "Pikachu"),
        ("charmander", "mew", "mew"),
        ("bulbasaur", "bulbasaur", "draw"),
    ],
)
def test_pelea_pokemon(pokemon_ejemplo, atacante, oponente, ganador):
    result = pokemon_ejemplo[atacante].battle(pokemon_ejemplo[oponente])
    assert result.lower() == ganador.lower()

    random.seed(42)
    result = pokemon_ejemplo[atacante].battle(pokemon_ejemplo[oponente])
    assert result.lower() == ganador.lower()


@pytest.mark.pokemon
@pytest.mark.create
@pytest.mark.happy_path
def test_mostrar_pokemon(pokemon_ejemplo):
    squirtle = pokemon_ejemplo["squirtle"]
    assert isinstance(squirtle, Pokemon)


@pytest.mark.pokemon
@pytest.mark.exception_handling
def test_str_ataque_invalido():
    exc = AtaqueInvalidoError()
    assert str(exc) == "Attack value must be greater than zero."


@pytest.mark.pokemon
@pytest.mark.exception_handling
def test_str_salud_invalida():
    exc = SaludInvalidaError()
    assert str(exc) == "Health value must be greater than zero."


@pytest.mark.pokemon
@pytest.mark.unit
def test_calcular_power_contra():
    pikachu = Pokemon("Pikachu", "Electric", 50, 35)
    squirtle = Pokemon("Squirtle", "Water", 40, 44)
    power = pikachu.calcular_power_contra(squirtle)
    assert power > 50


@pytest.mark.pokemon
@pytest.mark.battle
def test_battle_logic_completa():
    firemon = Pokemon("Firemon", "Fire", 60, 50)
    grassmon = Pokemon("Grassmon", "Grass", 60, 50)
    result1 = firemon.battle(grassmon)
    result2 = grassmon.battle(firemon)
    result3 = firemon.battle(firemon)

    assert result1 == "Firemon"
    assert result2 == "Firemon"
    assert result3 == "Draw"
