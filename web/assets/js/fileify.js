// Courtesy of Alwinfy

const fileify = form => {
        const die = str => {throw new Error(str)};
        if(!form instanceof HTMLFormElement)
          die("pls fileify a form");
        form.addEventListener("submit", function(ev) {
          Promise.all([].map.call(form.querySelectorAll("input[type=file]"),
              async function(inp) {
            if(!inp.name) die("file input need name");
            const file = inp.files[0] || die("No file selected");
            const filedata = document.createElement("input");
            filedata.type = "hidden";
            filedata.name = "_" + inp.name;
            filedata.value = escape(await (new Response(file)).text());
            form.appendChild(filedata);
          })).then(() => form.submit());
          ev.preventDefault();
        });
      };

      // client code
      const form = document.querySelector('form'); // change to suit needs
      fileify(form);