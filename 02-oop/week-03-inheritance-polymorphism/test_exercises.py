import pytest

from exercises import *


def test_animals():
    d, c, p = Dog("Rex"), Cat("Tom"), Puppy("Bit")
    assert d.describe() == "Rex says Woof"
    assert c.describe() == "Tom says Meow"
    assert p.describe() == "Bit says woof!"
    assert isinstance(p, Dog) and isinstance(p, Animal)
    with pytest.raises(NotImplementedError):
        Animal("x").speak()


def test_chorus():
    assert chorus([Dog("a"), Cat("b")]) == ["a says Woof", "b says Meow"]
    assert chorus([]) == []


def test_employee_manager():
    e = Employee("Eve", 50000)
    assert e.annual_pay() == 50000
    assert e.describe() == "Eve earns 50000"
    m = Manager("Max", 80000, [e])
    assert m.annual_pay() == 81000
    m.add_report(Employee("Bob", 1))
    assert m.annual_pay() == 82000
    assert m.describe() == "Max earns 82000"
    assert m.name == "Max" and m.salary == 80000


def test_manager_reports_copied_and_not_shared():
    src = []
    m1 = Manager("a", 1, src)
    m1.add_report(Employee("x", 1))
    assert src == []
    assert Manager("b", 1).reports == []
    m2 = Manager("c", 1)
    m3 = Manager("d", 1)
    m2.add_report(Employee("x", 1))
    assert m3.reports == []


def test_shape_is_abstract():
    with pytest.raises(TypeError):
        Shape()

    class Half(Shape):
        def area(self):
            return 1

    with pytest.raises(TypeError):
        Half()


def test_shapes():
    r, s, c = Rectangle(2, 3), Square(4), Circle(1)
    assert r.area() == 6 and r.perimeter() == 10
    assert s.area() == 16 and s.perimeter() == 16
    assert c.area() == pytest.approx(math.pi)
    assert c.perimeter() == pytest.approx(2 * math.pi)
    assert isinstance(s, Rectangle) and isinstance(s, Shape)
    assert r.describe() == "Rectangle area=6.00 perimeter=10.00"
    assert s.describe() == "Square area=16.00 perimeter=16.00"
    assert c.describe() == "Circle area=3.14 perimeter=6.28"


def test_total_and_largest():
    shapes = [Rectangle(1, 1), Square(3), Circle(1)]
    assert total_area(shapes) == pytest.approx(1 + 9 + math.pi)
    assert largest_shape(shapes) is shapes[1]
    assert largest_shape([]) is None
    assert total_area([]) == 0


def test_mro():
    assert D().who() == ["D", "B", "C", "A"]
    assert B().who() == ["B", "A"]
    assert C().who() == ["C", "A"]
    assert A().who() == ["A"]
    assert mro_names(D) == ["D", "B", "C", "A", "object"]
    assert mro_names(int) == ["int", "object"]


def test_duck_typing():
    class Rock:
        pass

    class Broken:
        quack = "not callable"

    assert make_it_quack([Duck(), Rock(), Robot(), Broken()]) == ["Quack!", "Beep quack"]
    assert make_it_quack([]) == []


def test_classify():
    assert classify(True) == "bool"
    assert classify(3) == "int"
    assert classify(3.5) == "float"
    assert classify("x") == "str"
    assert classify([1]) == "list"
    assert classify({}) == "other"
    assert classify(None) == "other"


def test_json_mixin():
    u = User("Sam", 30)
    assert u.to_json() == '{"age": 30, "name": "Sam"}'
    u2 = User.from_json(u.to_json())
    assert isinstance(u2, User)
    assert (u2.name, u2.age) == ("Sam", 30)


def test_counting_list():
    cl = CountingList([1, 2])
    assert cl.ops == 0
    cl.append(3)
    cl.extend(x for x in (4, 5))
    assert cl.ops == 3
    assert cl.pop() == 5
    assert cl.ops == 4
    assert cl == [1, 2, 3, 4]
    assert len(cl) == 4 and cl[0] == 1
    assert isinstance(cl, list)
    assert cl.pop(0) == 1
    assert CountingList().ops == 0


def test_report():
    r = SalesReport({"b": 2, "a": 1})
    assert r.title == "Sales"
    assert r.generate() == "== Sales ==\na: 1\nb: 2\n-- end --"
    assert BriefSalesReport({"a": 1}).generate() == "== Sales ==\na: 1"


def test_report_abstract():
    with pytest.raises(TypeError):
        Report()
