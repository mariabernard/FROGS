<!DOCTYPE html>
<!--
# Copyright (C) 2015 INRA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
-->
<html>
	<head>
		<title>FROGS Affiliation</title>
		<meta charset="UTF-8">
		<meta name="version" content="4.1.0">
		<!-- CSS -->
		<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/4.1.1/css/bootstrap.css"></link>
		<link rel="stylesheet" href="https://cdn.datatables.net/1.10.19/css/dataTables.bootstrap4.min.css"></link>
		<link href="https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css" rel="stylesheet"></link>
		<style type="text/css">
            #js-alert {
                width: 90%;
                margin-right: auto;
                margin-left: auto;
            }
            #content {
                width: 90%;
                margin-right: auto;
                margin-left: auto;
            }
            .clear {
                clear: both;
                height: 0px;
                width: 100%;
                float: none !important;
            }
            ul.nav-tabs {
				margin-bottom: 30px;
			}
			.page-item.active .page-link {
				z-index: 1;
				color: #fff;
				background-color: #8EADAC;
				border-color: #8EADAC;
				outline: none !important;
				box-shadow: none !important;
			}
			.btn {
				color: #fff;
				border:#8EADAC;
				background-color: #8EADAC;
			}
			.btn:focus, .btn:active {
				outline: none !important;
				box-shadow: none !important;
			}
			.btn:hover:enabled{
				color: #fff;
				border:#648a89;
				background-color: #648a89;
				cursor:pointer !important;
			}
			.pb-2, .py-2 {
				padding-bottom: 1.5rem !important;
				margin-bottom: 2rem !important;
				margin-top: 4rem !important;
			}
			.pb-2-first{
				padding-bottom: 1.5rem !important;
				margin-bottom: 2rem !important;
				margin-top: 1rem !important;
			}
			/* ##### THEME FOR CHECKBOXES ##### */
			.container {
				position: relative;
				padding-left: 0px;
				margin-bottom: 15px;
				cursor: pointer;
				-webkit-user-select: none;
				-moz-user-select: none;
				-ms-user-select: none;
				user-select: none;
			}

			/* Hide the browser's default checkbox */
			.container input {
				position: absolute;
				opacity: 0;
				cursor: pointer;
			}

			/* Create a custom checkbox */
			.checkmark {
				position: absolute;
				top: 0;
				left: 0;
				height: 20px;
				width: 20px;
				background-color: #8EADAC;
				border-radius: 5px;
				opacity:0.65;
			}

			/* On mouse-over, add a grey background color */
			.container:hover input ~ .checkmark {
				background-color: #648a89;
			}

			/* When the checkbox is checked, add a blue background */
			.container input:checked ~ .checkmark {
				background-color: #8EADAC;
				opacity:1;
			}

			/* Create the checkmark/indicator (hidden when not checked) */
			.checkmark:after {
				content: "";
				position: absolute;
				display: none;
			}

			/* Show the checkmark when checked */
			.container input:checked ~ .checkmark:after {
				display: block;
			}

			/* Style the checkmark/indicator */
			.container .checkmark:after {
				left: 7px;
				top: 3px;
				width: 6px;
				height: 10px;
				border: solid white;
				border-width: 0 3px 3px 0;
				-webkit-transform: rotate(45deg);
				-ms-transform: rotate(45deg);
				transform: rotate(45deg);
			}
			.highcharts-button > path{
				stroke:#fff !important;
				fill:#8EADAC !important;
			}
			g.highcharts-button{
				cursor:pointer !important;
			}
			g.highcharts-button:hover{
				color: #fff;
				border:#648a89;
				background-color: #648a89;
				background-color: #648a89;
				cursor:pointer !important;
			}
			<!--
			.selectpicker{
				 	background-color:rgb(100, 138, 137,0.25);
				 	border-color:#8EADAC;
			}
			.selectpicker:hover{
				 	background-color:rgb(100, 138, 137,0.25);
				 	border-color:#8EADAC;
			}
			-->
			option{
				color:green
			}
			option:active, option:hover {
			  outline: none !important;
			}

			/* make it red instead (with with same width and style) */
			option:active, option:hover {
			  box-shadow:red !important;
			  outline-color: red !important;
			}
			select { -webkit-border-radius:25px; -moz-border-radius:25px; border-radius:25px; } select:hover { background-color:gren; } option:hover { background-color:yellow; } option { -webkit-border-radius:25px; -moz-border-radius:25px; border-radius:25px; color:blue; background-color:yellow; }
						 
        </style>
		<!-- JS -->
		<script type="text/javascript" src="https://code.jquery.com/jquery-2.1.3.min.js"></script>
		<script type="text/javascript" src="https://code.highcharts.com/8.2.0/highcharts.js"></script>
		<script type="text/javascript" src="https://code.highcharts.com/8.2.0/modules/exporting.js"></script>
		<script type="text/javascript" src="https://cdn.datatables.net/1.10.19/js/jquery.dataTables.min.js"></script>
		<script type="text/javascript" src="https://cdn.datatables.net/1.10.19/js/dataTables.bootstrap4.min.js"></script>
		<script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.11.0/umd/popper.min.js" integrity="sha384-b/U6ypiBEHpOf/4+1nzFpr53nxSS+GLCkfwBdFNTxtclqqenISfwAzpKaMNFNmj4" crossorigin="anonymous"></script>
		<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/js/bootstrap.min.js" integrity="sha384-smHYKdLADwkXOn1EmN1qk/HfnUcbVRZyYmZ4qpPea6sjB/pTJ0euyQp0Mk8ck+5T" crossorigin="anonymous"></script>
		<script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-select/1.12.4/js/bootstrap-select.min.js"></script>
		<script type="text/javascript">
			/*
			 * HTMLTable.js 0.1.0 - HTMLTable Library
			 *
			 * Copyright (c) 2015 Escudie Frederic
			 * Licensed under the MIT (http://www.opensource.org/licenses/mit-license.php) license.
			 */
			function HTMLtable(e){var t,r,n=e,a=";";this.deleteColumns=function(e){for(var a=n.getElementsByTagName("tr"),o=0;o<a.length;o++){s=0;var i=a[o].getElementsByTagName("td");0==i.length&&(i=a[o].getElementsByTagName("th"));for(var v=0,s=0;s<t[1];s++)if(!r[o][s]){var f=i[v].getAttribute("colspan");if(null!=f)for(var m=0;f>m;m++){if(in_array(s+m,e)){var u=i[v].getAttribute("colspan");u-1==0?i[v].removeAttribute("colspan"):i[v].setAttribute("colspan",u-1)}if(null==i[v].getAttribute("colspan")){var h=i[v];a[o].removeChild(h),v--}}else if(in_array(s,e)){var h=i[v];a[o].removeChild(h),v--}v++}}l(),g()},this.filter=function(e,a){var l=new RegExp(e),g=new Array;null!=a&&a||(g.c0=!0);for(var o=n.getElementsByTagName("tr"),i=0;i<o.length;i++){f=0;var v=o[i].getElementsByTagName("td");if(0!=v.length)for(var s=0,f=0;f<t[1];f++)r[i][f]||(l.test(v[s].innerHTML)&&(g["c"+f]=!0),s++)}for(var m=new Array,u=0;u<t[1];u++)void 0===g["c"+u]&&m.push(u);this.deleteColumns(m)},this.getModel=function(){return n};var l=function(){for(var e=0,r=0,a=n.getElementsByTagName("tr"),l=0;l<a.length;l++){var g=0;e++;var o=a[l].getElementsByTagName("td");0==o.length&&(o=a[l].getElementsByTagName("th"));for(var i=0;i<o.length;i++){var v=o[i].getAttribute("colspan");g+=null==v?1:parseInt(v)}g>r&&(r=g)}t=new Array(2),t[0]=e,t[1]=r},g=function(){r=new Array(t[0]);for(var e=0;e<t[0];e++){r[e]=new Array(t[1]);for(var a=0;a<t[1];a++)r[e][a]=!1}for(var l=n.getElementsByTagName("tr"),g=0;g<l.length;g++){v=0;var o=l[g].getElementsByTagName("td");0==o.length&&(o=l[g].getElementsByTagName("th"));for(var i=0,v=0;v<t[1];v++)if(!r[g][v]){var s=0,f=0,m=o[i].getAttribute("rowspan");null!=m&&(s=parseInt(m)-1);var u=o[i].getAttribute("colspan");null!=u&&(f=parseInt(u)-1);for(var h=s;h>=0;h--)for(var y=f;y>=0;y--)(0!=h||0!=y)&&(r[g+h][v+y]=!0);i++}}};this.replace=function(e,a,l){var g=new RegExp(e);null==a&&(a=""),null==l&&(l="");for(var o=n.getElementsByTagName("tr"),i=0;i<o.length;i++){f=0;var v=o[i].getElementsByTagName("td");if(0!=v.length)for(var s=0,f=0;f<t[1];f++)if(!r[i][f]){var m=g.exec(v[s].innerHTML);null!=m&&(void 0===m[1]&&(m[1]=""),v[s].innerHTML=a+m[1]+l),s++}}},this.toCSV=function(){for(var e="",l=n.getElementsByTagName("tr"),g=0;g<l.length;g++){var o=l[g].getElementsByTagName("td");0==o.length&&(o=l[g].getElementsByTagName("th"));for(var i=0,v=0;v<t[1];v++)r[g][v]||(e+=o[i].innerHTML,i++),e+=a;e=e.substr(0,e.length-1)+"\n"}return e},l(),g()}var in_array=function(e,t){for(var r in t)if(t[r]==e)return!0;return!1};
			
			/*
			 * dataTableExtractor.plugin.js 0.1.0 - datatableExport Library
			 *
			 * Copyright (c) 2015 Escudie Frederic
			 * Licensed under the MIT (http://www.opensource.org/licenses/mit-license.php) license.
			 */
			!function(t){t.fn.datatableExport=function(a){var e={anchor_id:t(this).attr("id"),table_id:null,csv_separator:";",omitted_columns:[]},n=t.extend(e,a);if(!t(this).length)throw"The element where the datatableExport is called does not exist.";if(void 0==n.anchor_id)throw"The datatableExport plugin must be called on an element with id.";if(null==n.table_id)throw"You must set the table_id parameter in datatableExport plugin.";if(!t("#"+n.table_id))throw"The datatable '#"+n.table_id+"' cannot be retieve in DOM.";return this.each(function(){var a=t(this);a.on("click",function(){t.fn.datatableExport.csv(n.anchor_id,n.table_id,n.csv_separator,n.omitted_columns)})})},t.fn.datatableExport.cleanCellMarkup=function(a,e){t.parseHTML(e);t("#"+a).append('<div class="hidden data-tmp">'+e+"</div>"),t("#"+a+" .data-tmp").find("input").each(function(){var a="";a=t(this).is(":checkbox")?t(this).is(":checked")?"true":"false":t(this).val(),t(this).replaceWith(a)});var n=t("#"+a+" .data-tmp").text();return t("#"+a+" .data-tmp").remove(),n},t.fn.datatableExport.csv=function(a,e,n,i){var l="",r=t("#"+e).DataTable(),d=t("#"+e+" thead")[0],o=new HTMLtable(d.cloneNode(!0));o.deleteColumns(i),l+=o.toCSV();var c=r.rows().data();t.each(c,function(e,n){for(var r="",d=0;d<n.length;d++)-1==t.inArray(d,i)&&(r+='"'+t.fn.datatableExport.cleanCellMarkup(a,n[d])+'";');""!=r&&(r=r.slice(0,-1)),l+=r+"\n"}),t("#"+a+"-extract-csv").length||t("#"+a).append('<a id="'+a+'-extract-csv" href="data:text/csv;charset=UTF-8,'+encodeURI(l)+'" download="data.csv" style="display:none;"></a>'),t("#"+a+"-extract-csv")[0].click()}}(jQuery);
		</script>
		<script type="text/javascript">
			Highcharts.SVGRenderer.prototype.symbols.download = function (x, y, w, h) {
				var path = [
					// Arrow stem
					'M', x + w * 0.5, y,
					'L', x + w * 0.5, y + h * 0.7,
					// Arrow head
					'M', x + w * 0.3, y + h * 0.5,
					'L', x + w * 0.5, y + h * 0.7,
					'L', x + w * 0.7, y + h * 0.5,
					// Box
					'M', x, y + h * 0.9,
					'L', x, y + h,
					'L', x + w, y + h,
					'L', x + w, y + h * 0.9
				];
				return path;
			};
			
			/**
			 * Returns the string representation of the number. 
			 * @param pValue {Float} The number to process.
			 * @return {String} The string representation (example: 12856892.11111 => 12,856,892.11).
			 */
		    var numberDisplay = function( pValue ){
		    	var new_val = "" ;
		    	if( ("" + pValue + "").indexOf(".") != -1 ){
		    		new_val = pValue.toFixed(2).replace(/(\d)(?=(\d{3})+\b)/g, '$1,');
		    	} else {
		    		new_val = pValue.toFixed().replace(/(\d)(?=(\d{3})+\b)/g, '$1,');
		    	}
		        return new_val ;
		    }
		    
			/**
			 * Returns the HTML table representation of the data. 
			 * @param pTitle {String} The title of the table.
			 * @param pCategories {Array} The title of each column.
			 * @param pData {Array} 2D matrix with row and column data.
			 * @return {String} The HTML table representation.
			 */
			var table = function( pTitle, pCategories, pData  ) {
				// Header
				var table_header = '' ;
				var table_header_line = "" ;
				for(var idx = 0 ; idx < pCategories.length ; idx++){
					table_header_line += "      <th>" + pCategories[idx] + "</th>\n" ;
				}
				table_header += "    <tr>\n" + table_header_line + "    </tr>\n" ;
				table_header = "  <thead>\n" + table_header + "  </thead>\n" ;
				
				// Body
				var table_body = '' ;
				for(var data_idx = 0 ; data_idx < pData.length ; data_idx++){
					var table_body_row = "" ;
					for(var category_idx = 0 ; category_idx < pCategories.length ; category_idx++){
						if( typeof pData[data_idx][category_idx] === "number" ) {
							table_body_row += "      <td>" + numberDisplay(pData[data_idx][category_idx]) + "</td>\n" ;
						} else {
							table_body_row += "      <td>" + pData[data_idx][category_idx] + "</td>\n" ;
						}
					}
					table_body += "    <tr>\n" + table_body_row + "    </tr>\n" ;
				}
				table_body = "  <tbody>\n" + table_body + "  </tbody>\n" ;

				return '<table class="table table-striped table-bordered">\n' + table_header + table_body + "</table>\n" ;
			}
			
			// couleur des diapos : bleu #8EADAC, vert : #A2A32F, orange1 #C6792B , taupe #9A866C, orange pastel : #DE9F73
			var histogram_param = function( pTitle, pYTitle, pCategories, pSeries, unity ) {
				var param = {
					chart: {
						type: 'column'
					},
					colors : [
                            '#8EADAC', '#DE9F73'
                    ] ,
                    exporting:{buttons: {contextButton: { symbol: 'download' }}},
					buttons: {contextButton: {menuItems: ['downloadPNG', 'downloadSVG']}},
					navigation: {
						buttonOptions: {
							theme: {
								r: 4,
								fill:'#8EADAC',
								states: {
									hover: {
										fill: 'rgb(100, 138, 137)',
										stroke:'#8EADAC'
									},
									select: {
										stroke: '#8EADAC',
										fill: 'rgb(100, 138, 137)',
									}
								}
							}
						}
					},
					title: {
						text: pTitle
					},
					xAxis: {
						categories: pCategories,
						crosshair: true,
						crosshair: {
							color: "rgb(142,173,172,0.25)"
						}
					},
					yAxis: {
						min: 0,
						title: {
							text: pYTitle
						}
					},
					tooltip: {
						headerFormat: '<span style="font-size:10px">{point.key}</span><table>',
						pointFormat: '<tr><td style="color:{series.color};padding:0">{series.name}: </td>' +
							'<td style="padding:0"><b>{point.y} ' + unity + '</b></td></tr>',
						footerFormat: '</table>',
						shared: true,
						useHTML: true
					},
					plotOptions: {
						column: {
							pointPadding: 0.2,
							borderWidth: 0
						}
					},
					credits: {
						enabled: false
					},
					series: pSeries
				};
				
				return param ;
			}
			
			/**
			* Returns hash use to init HightChart object (without 'type'). 
			* @param pTitle {String} The title of the chart.
			* @param pXTitle {String} The xAxis title.
			* @param pYTitle {String} The yAxis title.
			* @param pXCategories {Array} The title of each category (x scale labels).
			* @param pData {Array} The HightChart series.
			* @return {Hash} The hash.
			* @warning This method use HightChart xAxis.categories.
			*/
			// couleur des diapos : bleu #8EADAC, vert : #A2A32F, orange1 #C6792B , taupe #9A866C, orange pastel : #DE9F73
			var chartplot = function( pTitle, pXTitle, pYTitle, pXCategories, pData ) {
				var chart = {
						title: {
							text: pTitle
						},
						colors : [
                            '#8EADAC', '#DE9F73'
                    	] ,
                    	exporting:{buttons: {contextButton: { symbol: 'download' }}},
						buttons: {contextButton: {menuItems: ['downloadPNG', 'downloadSVG']}},
						navigation: {
							buttonOptions: {
								theme: {
									r: 4,
									fill:'#8EADAC',
									states: {
										hover: {
											fill: 'rgb(100, 138, 137)',
											stroke:'#8EADAC'
										},
										select: {
											stroke: '#8EADAC',
											fill: 'rgb(100, 138, 137)',
										}
									}
								}
							}
						},
						xAxis: {},
						yAxis: {
							title: {
								text: pYTitle
							}
						},
						series: pData,
						credits: {
							enabled: false
						}
				}
				if( pXCategories != null ){
					chart['xAxis']['categories'] = pXCategories ;
				}
				if( pXTitle != null ){
					chart['xAxis']['title'] = { text: pXTitle } ;
				}
				if( pData.length <= 1 ) {
					chart['legend'] = {'enabled': false};
				} else {
					chart['legend'] = {'enabled': true};
				}
				return chart ;
			}
			
			var pie_param = function( pTitle, pData, unity ) {
				var series = [{
	                type: 'pie',
	                name: unity,
	                data: pData
            	}]
				var plot = chartplot( pTitle, null, null, null, series );
				plot['tooltip'] = {
		            pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
		        };
				plot['plotOptions'] = {
		            pie: {
		                allowPointSelect: true,
		                cursor: 'pointer',
		                dataLabels: {
		                    enabled: true,
		                    useHTML : true,
		                    formatter: function () {
        		                return this.point.name + ' : ' + numberDisplay(this.point.y);
		                    },
		                    style: {
		                        color: (Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black'
		                    }
		                }
		            }
		        };
				return plot ;
			};
			
			$(function() {
				var global_results = ###GLOBAL_DATA### ;
				var sample_results = ###SAMPLES_DATA### ;
				var taxonomy_ranks = ###TAXONOMY_RANKS### ;
				
				// Remove alert
				$('#js-alert').remove();
				$('#content').removeClass("hidden");
				
				// Display summary
				var std_color = Highcharts.getOptions().colors ;
			    Highcharts.getOptions().colors = Highcharts.map(Highcharts.getOptions().colors, function (color) {
			        return {
			            radialGradient: { cx: 0.5, cy: 0.3, r: 0.7 },
			            stops: [
			                [0, color],
			                [1, Highcharts.Color(color).brighten(-0.3).get('rgb')] // darken
			            ]
			        };
			    });
			    
				var pie_series = [
					["With affiliation", global_results["nb_clstr_with_affi"]],
					["Without affiliation", (global_results["nb_clstr"] - global_results["nb_clstr_with_affi"])]
				]
				$('#clstr-ratio-affi').highcharts( pie_param("OTUs affiliation", pie_series, 'OTUs') );
				
				var pie_series = [
					["With affiliation", global_results["nb_seq_with_affi"]],
					["Without affiliation", (global_results["nb_seq"] - global_results["nb_seq_with_affi"])]
				]
				$('#seq-ratio-affi').highcharts( pie_param("Sequences affiliation", pie_series, 'sequences') );
				
				Highcharts.getOptions().colors = std_color ;
				
				var histogram_series = [
					{
						'name': 'OTUs',
						'data': global_results["nb_clstr_ambiguous"].map(function(num) {
							var prct = (num/global_results["nb_clstr"])*10000/100 ;
							return( parseFloat(numberDisplay(prct)) );
						})
					}, {
						'name': 'Sequences',
						'data': global_results["nb_seq_ambiguous"].map(function(num) {
							var prct = (num/global_results["nb_seq"])*10000/100 ;
							return( parseFloat(numberDisplay(prct)) );
						})
					}
				];
				$('#clstr-multi-affi').highcharts( histogram_param('Multi-affiliation by taxonomic rank', '% of multi-affiliated', taxonomy_ranks, histogram_series, '%') );
				
				// Display data by sample
				var table_categories = [ 'Sample', 'Nb OTUs', '% OTUs affiliated by blast', 'Nb seq', '% seq affiliated by blast' ];
				var table_series = new Array();
				for( var sample_name in sample_results ){
					table_series.push([
						sample_name,
						sample_results[sample_name]['nb_clstr'],
						Math.round(((sample_results[sample_name]['nb_clstr_with_affi']/sample_results[sample_name]['nb_clstr'])*10000)/100),
						sample_results[sample_name]['nb_seq'],
						Math.round(((sample_results[sample_name]['nb_seq_with_affi']/sample_results[sample_name]['nb_seq'])*10000)/100)
					]);
				};
				$('#samples-details').append( table("Blast affiliation by sample", table_categories, table_series) );
				$('#samples-details table').prop( 'id', 'details-table' );
				$('#samples-details table').DataTable({
					//"sDom": '<"top"<"#details-csv-export"><"clear">lf>rt<"bottom"ip><"clear">'
					dom: 	"<'#details-csv-export'><'row'<'col-sm-5'l><'col-sm-7'f>>" +
							"<'row'<'col-sm-12'tr>>" +
							"<'row'<'col-sm-5'i><'col-sm-7'p>>",
							"pagingType": "simple"
				});
				$('#details-csv-export').html( '<button class="btn btn-primary" ><span class="fa fa-download" aria-hidden="true"> CSV</span></button>' );
				$('#details-csv-export').addClass( 'dataTables_filter' );
				$('#details-csv-export').datatableExport({
					'table_id': "details-table"
				});
			});
		</script>
	</head>
	<body>
		<p id="js-alert" class="alert alert-warning">
			javascript is needed to display data.<br />
			If you try to view this data on galaxy please contact your administrator to authorise javascript or download the file to view.
		</p>
		<div id="content" class="hidden">
			<div id="global-summary">
				<h2 class="pb-2-first mt-4 mb-2 border-bottom" style="margin-top: 1rem">Blast affiliation summary</h2>
				<div class="row">
					<div class="col-md-1"></div>
					<div id="clstr-ratio-affi" class="col-md-5"></div>
					<div id="seq-ratio-affi" class="col-md-5"></div>
					<div class="col-md-1"></div>
				</div>
				<h2 class="pb-2 mt-4 mb-2 border-bottom">Blast multi-affiliation summary</h2>
				<div class="row">
					<div class="col-md-1"></div>
					<div id="clstr-multi-affi" class="col-md-10"></div>
					<div class="col-md-1"></div>
				</div>
			</div>
			<div id="samples-details">
				<h2 class="pb-2 mt-4 mb-2 border-bottom">Blast affiliation by sample</h2>
			</div>
		</div>
	</body>
</html>
