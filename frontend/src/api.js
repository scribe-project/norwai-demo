export async function post(url, body) {
  return fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body,
  }).then((res) => res.json())
    .catch((err) => console.error(err));
}
