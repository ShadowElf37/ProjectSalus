function format(str) {
    if(arguments.length > 1) {
            const t = typeof arguments[1];
            const args = (t === 'string' || t === 'number')
                    ? Array.prototype.slice.call(arguments, 1)
                    : arguments[1];

            for(const key in args) {
                    str = str.replace(new RegExp('\\{' + key + '\\}', 'gi'), args[key]);
            }
    }
    return str;
}

function unique(array){
    return array.filter(function(value, index, self) { 
        return self.indexOf(value) === index;
    });
}