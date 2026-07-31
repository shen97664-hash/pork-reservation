import os

f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "admin_reservations.html")
c = open(f, "r", encoding="utf-8").read()

# Add delete button after each cancel button form
old = """                    </form>
                    {% elif r.status == 'confirmed' %}"""
new = """                    </form>
                    <form method="POST" action="{{ url_for('delete_reservation', res_id=r.id) }}" class="d-inline" onsubmit="return confirm('确定删除此预约吗？删除后库存会自动退回。')">
                        <button class="btn btn-outline-dark btn-sm" title="删除"><i class="bi bi-trash"></i></button>
                    </form>
                    {% elif r.status == 'confirmed' %}"""
c = c.replace(old, new)

# Add delete button after confirmed section cancel button
old2 = """                    </form>
                    {% else %}
                    <span class="text-muted">-</span>"""
new2 = """                    </form>
                    <form method="POST" action="{{ url_for('delete_reservation', res_id=r.id) }}" class="d-inline" onsubmit="return confirm('确定删除此预约吗？删除后库存会自动退回。')">
                        <button class="btn btn-outline-dark btn-sm" title="删除"><i class="bi bi-trash"></i></button>
                    </form>
                    {% else %}
                    <span class="text-muted">-</span>"""
c = c.replace(old2, new2)

# Add delete button for cancelled reservations
old3 = """                    {% else %}
                    <span class="text-muted">-</span>
                    {% endif %}"""
new3 = """                    {% else %}
                    <form method="POST" action="{{ url_for('delete_reservation', res_id=r.id) }}" class="d-inline" onsubmit="return confirm('确定删除此预约记录吗？')">
                        <button class="btn btn-outline-dark btn-sm" title="删除"><i class="bi bi-trash"></i></button>
                    </form>
                    {% endif %}"""
c = c.replace(old3, new3)

open(f, "w", encoding="utf-8").write(c)
print("admin_reservations.html updated OK")
