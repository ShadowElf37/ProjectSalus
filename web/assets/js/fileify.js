// Courtesy of Alwinfy

const fileify = form => {
  const die = str => {throw new Error(str)};
  if(!form instanceof HTMLFormElement)
    die("pls fileify a form");
  form.addEventListener("submit", ev => {
    const files = form.querySelectorAll("input[type=file]");
    let count = files.length;
    files.forEach(inp => {
      if(!inp.name) die("file input need name");
      const file = inp.files[0] || die("No file selected");
      const filedata = document.createElement("input");
      filedata.type = "hidden";
      filedata.name = "_" + inp.name;
      const reader = new FileReader();
      reader.addEventListener("loadend", () => {
        filedata.value = encodeURI(reader.result);
        form.appendChild(filedata);
        if(!--count)
          form.submit();
      });
      reader.readAsBinaryString(file);
    });
    ev.preventDefault();
    return false;
  });
};

/*
// client code
const form = document.querySelector('form'); // change to suit needs
fileify(form);
*/