/**
 * Helper class for getting colors
 */
var Colors = function() {};


Colors.all = [];
Colors.indexes = {};

Colors.add = function(name, hex) {
	Colors.all.push({
		name: name,
		hex: hex
	});
	Colors.indexes[name] = Colors.all.length - 1;
}

Colors.applyPercentage = function(hex, percentage) {
	if(percentage == 1)
		return hex;
	var rgb = [1, 3, 5];
	rgb = rgb.map(function(i){
		// console.log('percentage: ' + percentage);
		// console.log(i);
		i = parseInt(hex.substring(i, i + 2), 16);
		// console.log(i);
		i = parseInt(i * percentage);
		// console.log(i);
		i = Math.min(255, i);
		// console.log(i);
		i = Math.max(0, i);
		// console.log(i);
		i = i.toString(16);
		if(i.length < 2)
			i = '0' + i;
		// console.log(i);
		return i;
	});
	// console.log(rgb);
	return '#' + rgb.join('');
}

Colors.lighten = function(hex, percentage) {
	if(percentage === undefined)
		percentage = 0.25;
	return Colors.applyPercentage(hex, 1 + percentage);
}

Colors.darken = function(hex, percentage) {
	if(percentage === undefined)
		percentage = 0.25;
	return Colors.applyPercentage(hex, 1 - percentage);
}

Colors.get = function(id, percentage) {
	if(percentage === undefined)
		percentage = 1;
	if(typeof id === 'number'){
		return Colors.applyPercentage(Colors.all[id].hex, percentage);
	} else {
		if(Colors.indexes[id] !== undefined){
			return Colors.applyPercentage(Colors.all[Colors.indexes[id]].hex, percentage);
		} else {
			console.error('Colors: Unknown color name');
		}
	}
}

Colors.getDark = function(id, percentage) {
	return Colors.darken(Colors.get(id), percentage);
}

Colors.getLight = function(id, percentage) {
	return Colors.lighten(Colors.get(id), percentage);
}

Colors.sort = function(){
	Colors.all.sort(function(a, b){
		return a.name > b.name;
	});
}

Colors.add('Blue', '#0000FF');
Colors.add('Green', '#008000');
Colors.add('DarkBlue', '#00008B');
Colors.add('DarkCyan', '#008B8B');
Colors.add('DodgerBlue', '#1E90FF');
Colors.add('LightBlue', '#ADD8E6');
Colors.add('MidnightBlue', '#191970');
Colors.add('RoyalBlue', '#4169E1');
Colors.add('SkyBlue', '#87CEEB');
Colors.add('CadetBlue', '#5F9EA0');
Colors.add('DarkSlateBlue', '#483D8B');
Colors.add('SteelBlue', '#4682B4');
Colors.add('DarkOliveGreen', '#556B2F');
Colors.add('DarkSeaGreen', '#8FBC8F');
Colors.add('LawnGreen', '#7CFC00');
Colors.add('LightGreen', '#90EE90');
Colors.add('LightSeaGreen', '#20B2AA');
Colors.add('LimeGreen', '#32CD32');
Colors.add('MediumSeaGreen', '#3CB371');
Colors.add('SeaGreen', '#2E8B57');
Colors.add('SpringGreen', '#00FF7F');
Colors.add('YellowGreen', '#9ACD32');
Colors.add('BlueViolet', '#8A2BE2');
Colors.add('Brown', '#A52A2A');
Colors.add('BurlyWood', '#DEB887');
Colors.add('Chartreuse', '#7FFF00');
Colors.add('Chocolate', '#D2691E');
Colors.add('Coral', '#FF7F50');
Colors.add('Crimson', '#DC143C');
Colors.add('DarkGoldenRod', '#B8860B');
Colors.add('DarkGray', '#A9A9A9');
Colors.add('DarkKhaki', '#BDB76B');
Colors.add('DarkMagenta', '#8B008B');
Colors.add('DarkOrange', '#FF8C00');
Colors.add('DarkOrchid', '#9932CC');
Colors.add('DarkRed', '#8B0000');
Colors.add('DarkSalmon', '#E9967A');
Colors.add('DarkSlateGray', '#2F4F4F');
Colors.add('DarkViolet', '#9400D3');
Colors.add('DeepPink', '#FF1493');
Colors.add('DimGray', '#696969');
Colors.add('FireBrick', '#B22222');
Colors.add('Fuchsia', '#FF00FF');
Colors.add('Gold', '#FFD700');
Colors.add('GoldenRod', '#DAA520');
Colors.add('Gray', '#808080');
Colors.add('HotPink', '#FF69B4');
Colors.add('IndianRed', '#CD5C5C');
Colors.add('Indigo', '#4B0082');
Colors.add('LightCoral', '#F08080');
Colors.add('LightPink', '#FFB6C1');
Colors.add('LightSlateGray', '#778899');
Colors.add('Lime', '#00FF00');
Colors.add('Magenta', '#FF00FF');
Colors.add('Maroon', '#800000');
Colors.add('MediumAquaMarine', '#66CDAA');
Colors.add('MediumOrchid', '#BA55D3');
Colors.add('MediumVioletRed', '#C71585');
Colors.add('Olive', '#808000');
Colors.add('OliveDrab', '#6B8E23');
Colors.add('Orange', '#FFA500');
Colors.add('OrangeRed', '#FF4500');
Colors.add('Orchid', '#DA70D6');
Colors.add('PaleVioletRed', '#DB7093');
Colors.add('Peru', '#CD853F');
Colors.add('Pink', '#FFC0CB');
Colors.add('Plum', '#DDA0DD');
Colors.add('Purple', '#800080');
Colors.add('RebeccaPurple', '#663399');
Colors.add('Red', '#FF0000');
Colors.add('RosyBrown', '#BC8F8F');
Colors.add('SaddleBrown', '#8B4513');
Colors.add('Salmon', '#FA8072');
Colors.add('SandyBrown', '#F4A460');
Colors.add('Sienna', '#A0522D');
Colors.add('Silver', '#C0C0C0');
Colors.add('SlateGray', '#708090');
Colors.add('Tan', '#D2B48C');
Colors.add('Teal', '#008080');
Colors.add('Thistle', '#D8BFD8');
Colors.add('Tomato', '#FF6347');
Colors.add('Violet', '#EE82EE');
Colors.add('Yellow', '#FFFF00');

Colors.sort();
