/**
 * Additional methods for the Function objects
 */

/**
 * Gets list of parameter names of the function
 */
Function.prototype.getParameterNames = function() {
    return this.toString()
        .between('(', ')')
        .split(',')
        .map(function(name){
            return name.trim();
        })
        .filter(function(name){
            return name != '';
        });
}

/**
 * Gets the attributes of a var used in the code of the function
 * @param  {String} name The name of the var
 */
Function.prototype.getAttributesOf = function(name) {
    var regex = new RegExp("[^a-zA-Z0-9_$]+"  + name + "\\.[0-9a-zA-Z_$]+", 'g');
    var matches = this.toString().match(regex);
    if(matches)
        return matches.unique().map(function(expr){
            var parts = expr.split('.');
            return parts[1];
        });
    return [];
}
