import { useEffect, useState } from "react";
import { api } from "../api";


function ContactEditor({
  restaurantId,
  initialContact,
}) {
  const [officialName, setOfficialName] = useState(
    initialContact?.official_name || ""
  );
  const [email, setEmail] = useState(
    initialContact?.email || ""
  );
  const [phone, setPhone] = useState(
    initialContact?.phone || ""
  );
  const [active, setActive] = useState(
    initialContact?.active ?? true
  );
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function save() {
    setSaving(true);
    setMessage("");
    setError("");

    try {
      await api.saveOutletContact(
        restaurantId,
        {
          official_name: officialName,
          email: email || null,
          phone: phone || null,
          active,
        }
      );

      setMessage("Saved");
    } catch (err) {
      setError(
        err.message ||
          "Unable to save outlet contact."
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <div
      style={{
        marginTop: "10px",
        padding: "12px",
        background: "#f7f9f7",
        borderRadius: "10px",
        border: "1px solid #e2e8e2",
      }}
    >
      <input
        value={officialName}
        onChange={(event) =>
          setOfficialName(event.target.value)
        }
        placeholder="Official name"
        style={{ width: "100%", marginBottom: "7px" }}
      />

      <input
        value={email}
        onChange={(event) =>
          setEmail(event.target.value)
        }
        placeholder="Official email"
        type="email"
        style={{ width: "100%", marginBottom: "7px" }}
      />

      <input
        value={phone}
        onChange={(event) =>
          setPhone(event.target.value)
        }
        placeholder="Official phone"
        style={{ width: "100%", marginBottom: "7px" }}
      />

      <label
        style={{
          display: "flex",
          gap: "7px",
          alignItems: "center",
          fontSize: "12px",
          marginBottom: "9px",
        }}
      >
        <input
          type="checkbox"
          checked={active}
          onChange={(event) =>
            setActive(event.target.checked)
          }
        />
        Enable monthly notifications
      </label>

      <div
        style={{
          display: "flex",
          gap: "8px",
          alignItems: "center",
        }}
      >
        <button
          className="secondary-button"
          onClick={save}
          disabled={saving || !officialName.trim()}
        >
          {saving ? "Saving..." : "Save contact"}
        </button>

        {message && (
          <span style={{ color: "#27804d", fontSize: "12px" }}>
            {message}
          </span>
        )}

        {error && (
          <span style={{ color: "#b42318", fontSize: "12px" }}>
            {error}
          </span>
        )}
      </div>
    </div>
  );
}


export default function Establishments() {
  const [data, setData] = useState(null);
  const [contacts, setContacts] = useState({});
  const [editingId, setEditingId] = useState(null);
  const [loadingContacts, setLoadingContacts] = useState(false);

  useEffect(() => {
    let active = true;

    api.establishments()
      .then(async (result) => {
        if (!active) return;

        setData(result);

        const establishments = result?.establishments || [];

        setLoadingContacts(true);

        const loaded = {};

        await Promise.all(
          establishments.map(async (outlet) => {
            try {
              const response =
                await api.outletContact(outlet.id);
              loaded[outlet.id] = response.contact;
            } catch {
              loaded[outlet.id] = null;
            }
          })
        );

        if (active) {
          setContacts(loaded);
          setLoadingContacts(false);
        }
      })
      .catch(() => {
        if (active) {
          setData({ establishments: [] });
          setLoadingContacts(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <div className="eyebrow">REGIONAL REGISTER</div>
          <h2>Establishments</h2>
          <p className="muted">
            Outlet status, monitoring activity and monthly notification contacts.
          </p>
        </div>
      </div>

      <section className="section-card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Establishment</th>
                <th>Registration</th>
                <th>Region</th>
                <th>Devices</th>
                <th>Active alerts</th>
                <th>Critical</th>
                <th>Official contact</th>
              </tr>
            </thead>

            <tbody>
              {data?.establishments?.map((r) => {
                const contact = contacts[r.id];
                const editing = editingId === r.id;

                return (
                  <tr key={r.id}>
                    <td>
                      <strong>{r.name}</strong>
                      <small>{r.location}</small>
                    </td>

                    <td>{r.registration_id}</td>
                    <td>{r.region}</td>
                    <td>{r.devices}</td>
                    <td>{r.active_alerts}</td>

                    <td>
                      <span
                        className={
                          r.critical_alerts
                            ? "text-danger"
                            : "text-safe"
                        }
                      >
                        {r.critical_alerts}
                      </span>
                    </td>

                    <td style={{ minWidth: "230px" }}>
                      {loadingContacts && !contact ? (
                        <span className="muted">
                          Loading contact...
                        </span>
                      ) : editing ? (
                        <ContactEditor
                          restaurantId={r.id}
                          initialContact={contact}
                        />
                      ) : (
                        <div>
                          {contact ? (
                            <>
                              <strong>
                                {contact.official_name}
                              </strong>
                              <small>
                                {contact.email ||
                                  "No email"}
                                {contact.phone
                                  ? ` • ${contact.phone}`
                                  : ""}
                              </small>
                              <small>
                                {contact.active
                                  ? "Monthly notifications enabled"
                                  : "Notifications disabled"}
                              </small>
                            </>
                          ) : (
                            <span className="muted">
                              No contact configured
                            </span>
                          )}

                          <button
                            className="text-link"
                            style={{
                              border: "none",
                              background: "transparent",
                              padding: "4px 0",
                              cursor: "pointer",
                            }}
                            onClick={() =>
                              setEditingId(
                                editing ? null : r.id
                              )
                            }
                          >
                            {contact ? "Edit" : "Set contact"}
                          </button>
                        </div>
                      )}

                      {editing && (
                        <button
                          className="text-link"
                          style={{
                            border: "none",
                            background: "transparent",
                            padding: "4px 0",
                            cursor: "pointer",
                          }}
                          onClick={() =>
                            setEditingId(null)
                          }
                        >
                          Cancel
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
