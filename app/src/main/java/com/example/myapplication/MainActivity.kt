package com.example.rpgnames

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.material3.Button
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            RPGNameGeneratorApp()
        }
    }
}

@Composable
fun RPGNameGeneratorApp() {
    val races = listOf("Dark Elf", "Dwarf", "Elf", "Gnome", "Human", "Halfling", "Half Elf", "Half Orc", "Outsider")
    val presetNumbers = listOf(1, 3, 5, 10)
    val maleCounts = remember { mutableStateMapOf<String, String>() }
    val femaleCounts = remember { mutableStateMapOf<String, String>() }
    var globalPreset by remember { mutableStateOf(0) }
    var results by remember { mutableStateOf("") }

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp)
    ) {
        Text(
            text = "RPG Name Generator",
            fontSize = 32.sp,
            fontWeight = FontWeight.Bold
        )
        Spacer(Modifier.height(16.dp))

        races.forEach { race ->
            Card(
                Modifier
                    .fillMaxWidth()
                    .padding(vertical = 8.dp),
                elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
            ) {
                Column(Modifier.padding(12.dp)) {
                    Text(race, style = MaterialTheme.typography.titleMedium)
                    Spacer(Modifier.height(8.dp))
                    Row(
                        Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Column(Modifier.weight(1f).padding(end = 8.dp)) {
                            Text("Male")
                            TextField(
                                value = maleCounts[race] ?: "",
                                onValueChange = { maleCounts[race] = it },
                                Modifier.fillMaxWidth(),
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
                            )
                        }
                        Column(Modifier.weight(1f).padding(start = 8.dp)) {
                            Text("Female")
                            TextField(
                                value = femaleCounts[race] ?: "",
                                onValueChange = { femaleCounts[race] = it },
                                Modifier.fillMaxWidth(),
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
                            )
                        }
                    }
                }
            }
        }

        Spacer(Modifier.height(16.dp))
        Row(
            Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
            presetNumbers.forEach { number ->
                Button(onClick = { globalPreset = number }) {
                    Text(number.toString())
                }
            }
        }

        Spacer(Modifier.height(16.dp))
        Button(
            onClick = { results = generateNames(races, maleCounts, femaleCounts, globalPreset) },
            Modifier.fillMaxWidth()
        ) {
            Text("Generate")
        }

        Spacer(Modifier.height(16.dp))
        Text(
            text = results,
            Modifier
                .fillMaxWidth()
                .background(MaterialTheme.colorScheme.surface)
                .padding(12.dp)
        )
    }
}

fun generateNames(
    races: List<String>,
    maleCounts: Map<String, String>,
    femaleCounts: Map<String, String>,
    globalPreset: Int
): String {
    val builder = StringBuilder()
    races.forEach { race ->
        val maleCount = maleCounts[race]?.toIntOrNull() ?: globalPreset
        val femaleCount = femaleCounts[race]?.toIntOrNull() ?: globalPreset
        repeat(maleCount) {
            builder.append("$race (Male): ${RandomNameGenerator.getRandomName(race, "Male")}\n")
        }
        repeat(femaleCount) {
            builder.append("$race (Female): ${RandomNameGenerator.getRandomName(race, "Female")}\n")
        }
    }
    return builder.toString()
}

// All name data consolidated in one object
object RandomNameGenerator {
    // Dwarven lists
    private val dpa = NameLists.dpa
    private val dsm = NameLists.dsm
    private val dsf = NameLists.dsf
    private val dca = NameLists.dca
    // Elven lists
    private val ena = NameLists.ena
    private val enb = NameLists.enb
    private val enc = NameLists.enc
    private val end = NameLists.end
    private val eme = NameLists.eme
    private val efe = NameLists.efe
    // Human lists
    private val hmn = NameLists.hmn
    private val hfn = NameLists.hfn
    private val hsn = NameLists.hsn
    // Gnome lists
    private val gmn = NameLists.gmn
    private val gfn = NameLists.gfn
    private val gcn = NameLists.gcn
    private val gms = NameLists.gms
    private val gfs = NameLists.gfs
    private val gcs = NameLists.gcs
    // Half Orc lists
    private val homp = NameLists.homp
    private val homs = NameLists.homs
    private val hofp = NameLists.hofp
    private val hofs = NameLists.hofs
    private val hoc  = NameLists.hoc
    private val howt = NameLists.howt
    // Half Elf lists
    private val hemp = NameLists.hemp
    private val hems = NameLists.hems
    private val hefp = NameLists.hefp
    private val hefs = NameLists.hefs
    // Outsider lists
    private val omn = NameLists.omn
    private val ofn = NameLists.ofn
    private val ot  = NameLists.ot
    // Halfling lists
    private val halflingMale = NameLists.halfling_male_names
    private val halflingFemale = NameLists.halfling_female_names
    private val halflingLast = NameLists.halfling_last_names

    // Naming functions
    private fun dwrfm() = "${dpa.random()}'${dsm.random()} ${dca.random()}"
    private fun dwrff() = "${dpa.random()}'${dsf.random()} ${dca.random()}"
    private fun em1() = "${ena.random()}'${enb.random()}${eme.random()} ${enc.random()}${end.random()}"
    private fun em2() = "${ena.random()}'${enb.random()}${eme.random()}"
    private fun em3() = "${ena.random()}'${enb.random()}'${enb.random()}${eme.random()} ${enc.random()}'${end.random()}"
    private fun em4() = "${enc.random()}'${ena.random()}${eme.random()} ${end.random()}${enc.random()}"
    private val emnfunct = listOf(::em1, ::em2, ::em3, ::em4)
    private fun ef1() = "${ena.random()}'${enb.random()}${efe.random()} ${enc.random()}${end.random()}"
    private fun ef2() = "${ena.random()}'${enb.random()}${efe.random()}"
    private fun ef3() = "${ena.random()}'${end.random()}'${enb.random()}${efe.random()} ${enc.random()}'${end.random()}"
    private val efffunct = listOf(::ef1, ::ef2, ::ef3)
    private fun hem1() = "${hmn.random()} ${hmn.random()} ${enc.random()}${end.random()}"
    private fun hem2() = "${hmn.random()} ${enc.random()}${end.random()}"
    private fun hem3() = "${hemp.random()}'${hems.random()} ${hsn.random()}"
    private fun hem4() = "${hemp.random()}'${hems.random()}${eme.random()} ${hsn.random()}"
    private fun hem5() = "${hemp.random()}'${hems.random()}${eme.random()}"
    private val hemnfunct = listOf(::hem1, ::hem2, ::hem3, ::hem4, ::hem5)
    private fun hef1() = "${hefp.random()}'${hefs.random()}${efe.random()} ${hsn.random()}"
    private fun hef2() = "${hefp.random()}'${hefs.random()} ${hsn.random()}"
    private fun hef3() = "${hefp.random()}'${hefs.random()}${efe.random()}"
    private fun hef4() = "${hfn.random()} ${enc.random()}${end.random()}"
    private fun hef5() = "${hfn.random()} ${enc.random()}${end.random()}"
    private val hefffunct = listOf(::hef1, ::hef2, ::hef3, ::hef4, ::hef5)
    private fun gnm1() = "${gmn.random()} ${gcn.random()}"
    private fun gnm2() = "${gms.random()} ${gcs.random()}"
    private val gnfunct = listOf(::gnm1, ::gnm2)
    private fun gnf1() = "${gfn.random()} ${gcn.random()}"
    private fun gnf2() = "${gfs.random()} ${gcs.random()}"
    private val gmfunct = listOf(::gnf1, ::gnf2)
    private fun hom1() = "${homp.random()}${homs.random()} ${hoc.random()}"
    private fun hom2() = "${homp.random()}${homs.random()} ${howt.random()} ${hoc.random()}"
    private fun hom3() = "${homp.random()} ${howt.random()} ${hoc.random()}"
    private val homfunc = listOf(::hom1, ::hom2, ::hom3)
    private fun hof1() = "${hofp.random()}${hofs.random()} ${hoc.random()}"
    private fun hof2() = "${hofp.random()}${hofs.random()} ${howt.random()} ${hoc.random()}"
    private fun hof3() = "${hofp.random()} ${howt.random()} ${hoc.random()}"
    private val hoffunc = listOf(::hof1, ::hof2, ::hof3)
    private fun dem1() = dwrfm()
    private fun dem2() = dwrff()
    private val functiondem = listOf(::dem1, ::dem2)
    private fun def1() = ef1()
    private fun def2() = ef2()
    private val functiondef = listOf(::def1, ::def2)

    fun getRandomName(race: String, gender: String): String {
        return when (race to gender) {
            "Dark Elf" to "Male"   -> dem1()
            "Dark Elf" to "Female" -> def1()
            "Elf" to "Male"        -> emnfunct.random()()
            "Elf" to "Female"      -> efffunct.random()()
            "Half Elf" to "Male"   -> hemnfunct.random()()
            "Half Elf" to "Female" -> hefffunct.random()()
            "Human" to "Male"      -> hmn.random()
            "Human" to "Female"    -> hfn.random()
            "Dwarf" to "Male"      -> dwrfm()
            "Dwarf" to "Female"    -> dwrff()
            "Halfling" to "Male"   -> halflingMale.random()
            "Halfling" to "Female" -> halflingFemale.random()
            "Outsider" to "Male"   -> omn.random()
            "Outsider" to "Female" -> ofn.random()
            "Gnome" to "Male"      -> gnfunct.random()()
            "Gnome" to "Female"    -> gmfunct.random()()
            "Half Orc" to "Male"   -> homfunc.random()()
            "Half Orc" to "Female" -> hoffunc.random()()
            else                      -> "Unnamed"
        }
    }
}

// Separate file: NameLists.kt
object NameLists {
    val dpa = listOf("Al","Andvar","Andvari","An","Ann","Annun","Aust","Auster","Anzan","Anzanil","Bal","Bali","Bar","Bara","Baraz","Bard","Bardin","Baru","Baruk","Blain","Bo","Bof","Bofurr","Bom","Bomburr","Bor","Bori","Bran","Brand","Bond","Bondu","Dai","Dainn","Dol","Dolg","Duf","Dufor","Dufr","Dur","Durinn","Eik","Eiken","Farin","Fil","Fili","Fimbul","Forn","Frar","Fros","Frost","Frosti","Furd","Gim","Ginnar","Glo","Gro","Han","Hannar","Hepti","Hor","Jari","Khaz","Khazad","Khel","Kheled","Kib","Kili","Lit","Lofar","Maez","Marz","Nar","Nibli","Nithi","Nothri","Nyr","Oinn","Onarr","Ori","Shathur","Sog","Sognir","Sothri","Thek","Thrashir","Thori","Thror","Vaestri","Varen","Vargin","Viggr","Vin","Vind","Vir","Virfir","Vitr","Zin","Zinbar","Zira","Ziral")
    val dsm = listOf("Aim","Ain","Aer","Ak","Ar","Ard","Ber","Bere","Bir","Bin","Dak","Dek","Dal","Din","El","Erl","Gal","Gan","Gar","Gath","Gen","Gur","Guk","Ik","Ias","Ili","Ir","Kas","Kral","Oril","Orik","Rak","Ral","Ric","Rid","Ster","Stili","Thal","Then","Thil","Thur","Ur","Urrur","Urt","Unt","Val","Var","Vili")
    val dsf = listOf("Aed","Ala","Alaca","Alsia","Ana","Ani","Astr","Bela","Beka","Bena","Bo","Bryn","Deih","Dis","Dred","Dris","Drus","Esli","Gret","Gunn","Hild","Ia","Iess","Ila","Ild","Kara","Lin","Lydd","Mora","Moa","Ola","Ora","Ona","Re","Rra","Ren","Serd","Shar","Thra","Tia","Tryd","Unn","Wynn","Ya","Yod")
    val dca = listOf("Arrowmen","Axebreaker","Axe Hammer","Ashen Forge","Blackbands","Craighold","Crystal Shield","Deep Creagsman","Dark Dwellers","Dirge Bane","Foe Hammer","Frost Bearers","Forge Worn","Fissure Kin","Fire Beards","Gold Bounds","Grim Scavengers","Grave Spine","Gem Hoards","Hollow Bones","Hammer Dashers","Hazel Axes","Iron Skull","Iron Born","Iron Spine","Iron Fist","Jade Carver","Krack Hammers","Light Bringeres","Long Beards","Lords of Gemfold","Long Claw","Lords of the Cliff","Mithrilborn","Metal Folders","Metal Born","Mithril Axes","Metal Blades","Metal Shaper","Mountaineer","Mount Hall","Night Shadows","Night Shaper","Night Bender","Night Warrior","Nightingale","Night Born","Orc Foe","Orc Grinder","Orc Horn","Orc Slayers","Ord Raiders","Oaken Maul","Oaken Tower","Onyx Raider","Onyx Born","Onyx Shield","Quartz Eater","Quartz Shield","Quartz Shaper","Racoon Raiders","Rusty Nails","Rising Suns","Rolling Stoned","Red Blades","Red Wrath","River Wrights","Rockjaw","Ram Raiders","Silver Beards","Stone Hammer","Sky Lords","Sword Breakers","Steel Beards","Steel Shapers","Spirals","Spiral Blades","Spire Forged","Spire Guard","Storm Hammer","Storm Foe","Storm Raiders","Thunder Kings","Thunder Riders","Thunder Shield","Tornado Raiders","Titan Sons","Thunder Lords","Thunder Born","Under Forge","Unkempt","Violet Hammer","Violet Shield","Winter Born","Yew Hammer","Yew Smith","Yarrowsmight")
    val ena = listOf("Ael","Aer","Aev","Al","Am","Ama","An","Ar","Ari","Arl","Arn","Bael","Bes","Cael","Cas","Cla","Cor","Dae","Dre","Dru","Du","Eav","Eil","Eir","Er","Ero","Eso","Est","Fa","Fai","Fera","Fi","Fin","Fir","Fis","Gael","Gai","Gau","Gar","Gil","Git","Ha","Har","Hu","Hue","Ia","Il","Iy","Iv","Ja","Jae","Jal","Jar","Jat","Ka","Kan","Kat","Ker","Kes","Keth","Koeh","Kor","Ky","Kyt","La","Lae","Laf","Lam","Lan","Lar","Las","Lat","Lve","Lvi","Ly","Lys","Mai","Mal","Mar","Mys","Na","Nim","Ny","Rae","Re","Rei","Ren","Res","Rhy","Rv","Ru","Sae","Seah","Si","Ta","Th","Ti","Uth","Ver","Vo")
    val enb = listOf("Ae","Ael","Aias","Aith","Al","Ali","Am","Ama","An","Ar","Ari","Aro","As","Ath","Ave","Avel","Bai","Bae","Brar","Ca","Can","Cav","Dar","De","Dre","Dri","Dul","Ean","El","Eli","Emar","En","Er","Eri","Evar","Fel","Hal","Har","Ias","Iat","Ik","Il","Im","Ir","Ith","Kas","Kash","Ki","Lan","Mah","Mil","Mus","Nal","Ni","Onn","Onna","Or","Oth","Que","Qui","Quis","Ra","Rah","Rad","Rail","Re","Reil","Reth","Rd","Ros","Ru","Ruil","Sai","Sal","San","Sel","Sha","Spar","Tae","Tas","Th","Thal","Thar","Ther","Thi","Thus","Ti","Tril","Ual","Uath","Us","Van","Var","Vus","Vas","Wyn","Ya","Yi","Yir","Yth","Za","Zair","Zy")
    val enc = listOf("Alea","Alean","Aliea","Ara","Arabi","Arken","Arkemea","Auvrea","Baequi","Ban","Banni","Cy","Cytis","Cyern","Di","Dir","Dirth","Dre","Dry","Dryier","Dwi","Dwin","Eil","Eyl","Eyllis","Eyth","Eyther","Fre","Frean","Freani","Gy","Gys","Gysse","Hea","Heasi","Hlea","Hun","Hunith","Ken","Kenn","Kennyr","Kille","Mae","Maern","Mel","Melith","Myr","Myrth","Nor","Norre","Orl","Orle","Ous","Oussea","Ri","Ril","Rilynn","Tea","Teas","Teasan","Tyr","Tyrnea","Vor","Vorran","Vis","Vist","Wier","Wyn","Yur","Zar","Zex")
    val end = listOf("Alt","Alti","Altin","Ane","Anea","Ann","Anni","Annia","Aear","Arnith","Atear","Ati","Atis","Athem","Caar","Con","Dis","Dlves","Elrvis","Epcith","Attln","Gis","Ghis","Ghynna","Itryn","Lylth","Mit","Mito","Mitore","Na","Nae","Nar","Nas","Nddare","Nel","Nedeth","Neldth","Rae","Raheal","Ret","Roetyn","Sat","Seti","Sith","Sither","Tha","The","Thi","Thy","Thyn","Thym","Tiarn","Tlit","Tlithat","Ty","Tyl","Tylar","Unden","Urd","Urddiren","Val","Valso","Vir","Virr","Virrea","Zea","Zaes")
    val eme = listOf("dir","ion","on")
    val efe = listOf("el","eth","es","wen","iel","ien","il")
    val hmn = listOf("Jaiden","Adriel","Rishi","Gage","Thomas","Eric","Aden","Tony","Jayson","Elvis","Joe","Graham","Korbin","Cristopher","Hugh","Talon","Noel","Benjamin","Alden","Malakai","Jalen","Grant","Troy","Kristopher","Javier","Zachery","Elisha","Armando","Donald","Mark","Julien","Lamar","Brian","Ronin","Jovanni","Roberto","Bryce","Niko","Simeon","Ronnie","Dominick","Alonso","Micheal","Russell","Konner","Zayden","Cullen","Tyson","Tyree","Zain","Lane","Moises","Juan","Kelvin","Kenny","Irvin","Steve","Cristian","Rigoberto","Kamron","Brayan","Austin","Brayden","Javon","Donte","Aedan","Trevon","Gunner","Damion","Isaias","Rowan","Maximus","Colby","Marshall","Jaylon","Chace","Efrain","Hector","Patrick","Owen","London","Antwan","Cash","Billy","Emilio","Cameron","Trevor","Vance","Jovany","Gauge","Keenan","Skylar","Leonel","Jacob","Leonidas","Makhi","Andre","Roy","Gael","Coby")
    val hfn = listOf("Fatima","Ashanti","Essence","Jaiden","London","Adelaide","Isabella","Leyla","Maci","Briley","Shirley","Melanie","Siena","Adalyn","Jessie","Cassie","Kayden","Aubrie","Hannah","Shannon","Gabrielle","Diamond","Amiah","Cora","Jenna","Jaycee","Elisa","Katelyn","Mayra","Melody","Presley","Frida","Guadalupe","Haylie","Kylee","Jordyn","Johanna","Lesly","Kristin","Brooklyn","Georgia","Anaya","Imani","Raelynn","Litzy","Juliet","Jada","Mariah","Zaniyah","Lillian","Brittany","Kaley","Leah","Celia","Victoria","Kyleigh","Tatiana","Skye","Lainey","Skyla","Jade","Kinley","Emely","Mya","Kierra","Ava","Sandra","Rachael","Brooke","Thalia","Anne","Karlie","Logan","Lola","Jolie","Margaret","Avah","Bailee","Mylee","Shyla","Mariana","Reagan","Alyssa","Jordin","Amiyah","Tiana","Aniya","Janet","Alannah","Meredith","Kamryn","Sharon","Jazmin","Jaida","Allie","Carolyn","Mariela","Deanna","Shyanne","Jaden")
    val hsn = listOf("Peterson","Stevens","Wilcox","Horn","Peters","Duke","Farmer","Melendez","Schneider","Jarvis","Bell","Marks","Dennis","Watson","Fisher","Mejia","Hendricks","Pitts","Reyes","Clements","Shields","Mata","Rubio","Holt","Collins","Lyons","Hopkins","Ochoa","Boone","Mayo","Harper","Giles","Reeves","Ibarra","Pena","Parsons","West","Shepherd","Anderson","Griffin","Huang","Duffy","Mcdowell","Velez","Cochran","Petty","Underwood","Coffey","Mcknight","Smith")
    val gmn = listOf("Anders","Alexander","Alf","Adolph","Aabram","Agmund","Balle","Baltzar","Bartolomus","Benot","Borgulf","Caspar","Christer","Claes","Clauus","Conkadus","Detlef","Didrik","Din","Dinus","Dorde","Dynius","Dyre","Efraim","Einar","Elef","Farmund","Felix","Folkar","Frans","Fridhi","Gabriel","Gsalen","Gervast","Habram","Helvi","Henrik","Holte","Ilias","Ingevald","Isaac","Ivar","Ionis","Jakobus","Joanus","Jurgen","Jovan","Kadhorn","Kasten","Kylva","Lars","Larentis","Lek","Linder","Lisman","Lucas","Magnill","Magnus","Marchus","Marten","Mickel","Mundo","Nicholas","Niels","Niklas","Nikomedus","Nurdman","Nis","Odhin","Ofradh","Oghmund","Ola","Olaf","Orikus","Ormulf","Ottoa","Paval","Peder","Petri","Philipus","Radholf","Rael","Rasmus","Rikulf","Roland","Salmund","Severin","Siomar","Thielvar","Throk","Thorald","Ubbe","Ulfger","Ummulf","Vaghn","Vallmar","Veseti","Villam","Ybba","Yrian")
    val gfn = listOf("Adelisse","Agnis","Aleka","Annika","Constantia","Cristin","Dordi","Dorothea","Elsa","Estrid","Eva","Filippa","Fastridh","Greta","Gynna","Hanna","Helena","Hilla","Halgha","Ida","Iliana","Ingerth","Ingridh","Justina","Johanna","Katarina","Kelo","Kristin","Katilvi","Lena","Lucia","Magdaalena","Maeritta","Raqna","Rikiza","Sibilla","Sighne","Sophia","Susanna","Svena","Thora","Torny","Unna","Ursula","Vendela","Vifrith","Yliana","Odha","Ohdild","Olfva")
    val gcn = listOf("Axelman","Bobbyknocker","Brinesniffs","Caramuls","Dickman","Erasnuffs","Flippurs","Fizzles","Geoshap","Gembitters","Hackles","Hareman","Ironknupps","Jumpham","Kilomun","Muckbutt","Nicklesoff","Rimbitter","Rounders","Sarps","Supplenupple","Tartman","Titisus","Vatsman","Whipplesniff")
    val gms = listOf("Abrasha","Aleksandr","Aleksei","Anatoli","Arkadi","Boris","Dmitiri","Efrem","Feliks","Filipp","Fyodor","Gavrill","Gennadi","Georgy","Grigori","Ilia","Illarion","Josef","Irinei","Iva","Khristofor","Kirill","Konstantin","Kostya","Lazar","Lev","Luka","Makari","Maksin","Michail","Misha","Moisey","Nazariy","Nokilai","Nikov","Odissey","Oleg","Petya","Sasha","Semyon","Valerian","Vssily","Viktor","Vitali","Vladimir","Yegor","Yelisey","Yuri","Zakhar","Zinovy")
    val gfs = listOf("Agnessa","Aksinia","Alexandria","Alisa","Anastasia","Anjelika","Arisha","Darya","Eleonora","Elmira","Elvira","Faina","Galina","Inessa","Irina","Julia","Kamilla","Karina","Katerina","Katia","Kiara","Kesnia","Lara","Larisa","Lena","Lilia","Marina","Mila","Milena","Nadia","Natasia","Natazi","Natalya","Nika","Oksana","Olya","Roksana","Sabina","Sashenka","Sofia","Tatianya","Valeria","Veronika","Viktoria","Vitaliya","Yelena","Yulia","Zinaida")
    val gcs = listOf("Amberfern","Anvilmuncher","Bingbong","Bubblens","Copperbang","Crumplestilts","Darkputter","Dustsniffers","Emberflue","Earthumper","Fairygrind","Feelervents","Gemstuffers","Gumbodancers","Hairglewen","Hopper","Ironpicks","Jinkglers","Jumpypouch","Kurmudump","Kugkig","Lumps","Littlelizard","Masons","Muppets","Marf","Nubbles","Nertsniffin","Nippletwist","Onyxians","Orbitars","Oddholes","Porcopines","Poffles","Quippers","Quickbitters","Reggieheds","Raptors","Skedaddlers","Snolligosh","Squippers","Spiffen","Topsys","Twaddlers","Tyrannos","Umbras","Vixers","Vippers","Whippersarpous","Waffleirn")
    val homp = listOf("Ara","Aram","Aran","Az","Azr","Azruk","Br","Bra","Brab","Brak","Brakru","Bru","Brud","Brudo","Cr","Cra","Cradu","Cre","Crer","Crerm","Cre","Dr","Dra","Drak","Dro","Drord","Du","Dur","Duri","Gr","Gra","Grab","Gn","Gnuz","Gnuu","Hr","Hro","Hror","Ke","Ker","Kerd","Kir","Kr","Kri","Lo","Loz","Lozru","Mh","Mhum","Nel","Nelra","Ner","Nerth","No","Nolm","Nolmp","Ol","Ola","Old","Or","Ord","Ordd","Ra","Raal","Ro","Ronth","Ror","Rorkra","Roth","Sig","Sigur","Thar","Thard","Yl","Yler","Ylerm","Zr","Zro","Zrom")
    val homs = listOf("aalrog","alrog","dredi","ell","ert","evik","gell","gory","irk","kas","kat","krurg","lak","lok","nolm","olch","olm","ory","rall","ram","redi","rert","rirg","rirk","rurg","rish","rmp","tuss","urk","vik")
    val hofp = listOf("Bu","Burg","Em","Emli","Emlis","Fa","Fay","Fayayg","Gr","Gron","Grong","Ha","Hal","Hali","Han","Hanl","Id","Iden","Mi","Mir","Mirth","Na","Nan","Nag","Nagna","Ni","Nid","Nidre","Oo","Oon","Oong","Ov","Ova","Ovak","Oval","Ovan","Ovas","Ra","Ragud","Re","Rel","Rela","Rell","Rella","Rellan","Rh","Rhi","Rhirt","Rhis","Ri","Rirth","Ye","Yeve","Yr","Yrsai")
    val hofs = listOf("ag","agu","an","anl","anla","ans","ansif","am","ama","amaith","bith","en","ena","enlah","gu","kish","koh","lana","llah","nah","ona","re","resh","ri","rish","runix","ut","uth","utta","vu","vux")
    val hoc  = listOf("Black Tusk","Broken Crag","Crimson Blade","Crooked Scar","Dark Shield","Death Maul","Flaming Fist","Frost Axe","Green Hand","Iron Claw","Shadow Dagger","Shattered Fang","Splintered Bone","Thunder Wolf","Thousand Spear")
    val howt = listOf("Ashen Protector","Battle Born","Battle Forged","Battle Heart","Berserker","Blind Eye","Crimson War Dancer","Dusk Bound","Earth Shaker","Fearless Hero","Honor Bound","Iron Fist","Land of Giants","Mighty Rage","Mountain Guardian","War Dancer","Wolf Raider","Wolf Rider")
    val hemp = listOf("Ael","Aer","Al","Alth","Althir","Ar","Arfin","Cel","Celth","Cur","Da","Dag","Dagliom","Dand","Dae","Daero","El","Elis","Elo","Erim","Faen","Findir","Gil","Gilin","Gilion","Il","Ilth","Ils","Ir","Irin","Leg","Man","Mar","Mel","Nahan","Nel","Orm","Orn","Orndir","Sil","Than","Thel","Thirm","Thran","Thro")
    val hems = listOf("Alea","Alean","Aliea","Ara","Arabi","Arken","Arkemea","Auvrea","Baequi","Ban","Banni","Cy","Cytis","Cyern","Di","Dir","Dirth","Dre","Dry","Dryier","Dwi","Dwin","Eil","Eyl","Eyllis","Eyth","Eyther","Fre","Frean","Freani","Gy","Gys","Gysse","Hea","Heasi","Hlea","Hun","Hunith","Ken","Kenn","Kennyr","Kille","Mae","Maern","Mel","Melith","Myr","Myrth","Nor","Norre","Orl","Orle","Ous","Oussea","Ri","Ril","Rilynn","Tea","Teas","Teasan","Tyr","Tyrnea","Vor","Vorran","Vis","Vist","Wier","Wyn","Yur","Zar","Zex")
    val hefp = listOf("Ael","Aerith","Anas","Anastri","Arw","Assar","Bra","Bralia","Celthi","Cym","Daen","Daenel","Dag","Dal","Dalia","Elan","Gal","Il","Ilth","Ir","Isa","Isabe","Mara","Mel","Nela","Nyra","Nyrie","Sev","Seva","Syl","Sylia","Tal","Talia","Tall")
    val hefs = listOf("Alt","Alti","Altin","Ane","Anea","Ann","Anni","Annia","Aear","Arnith","Atear","Ati","Atis","Athem","Caar","Con","Dis","Dlves","Elrvis","Epcith","Attln","Gis","Ghis","Ghynna","Itryn","Lylth","Mit","Mito","Mitore","Na","Nae","Nar","Nas","Nddare","Nel","Nedeth","Neldth","Rae","Raheal","Ret","Roetyn","Sat","Seti","Sith","Sither","Tha","The","Thi","Thy","Thyn","Thym","Tiarn","Tlit","Tlithat","Ty","Tyl","Tylar","Unden","Urd","Urddiren","Val","Valso","Vir","Virr","Virrea","Zea","Zaes")
    val omn = listOf("Belphegor","Cyndrath","Draven","Draxis","Draxor","Eldrin","Erebus","Jorath","Kaltor","Karnath","Khaldrin","Korrick","Kryzis","Lucifex","Lyrathis","Malakar","Mordekai","Morgath","Riven","Rynar","Thalgrim","Threnos","Thorak","Thorian","Varek","Vesperath","Xaltheron","Zaruk","Zaroth","Zorath","Zypharion")
    val ofn = listOf("Astra","Cassadra","Cynder","Elysian","Fendrel","Gora","Inferis","Isolde","Kaelith","Kaldra","Kora","Lilith","Lilithar","Lunara","Maris","Morrigane","Morrigann","Nera","Nerith","Nyx","Nyxara","Raventhorne","Seraph","Selene","Thaldrin","Thal","Thalia","Thara","Umbrosia","Vespa","Vespara","Zara")
    val ot = listOf("Cinderforge","Crimsonheart","Crimsonsoul","Darkspire","Devourer of Planets","Duskweaver","Duskmantle","Eater of Souls","Eldrith","Emberwind","Emberwing","Felspark","Frostveil","Frostwhisper","Gloomshade","Hallowshade","Loonshade","Moonshadow","Nightbloom","Sablewhisp","Shadowfist","Starforge","Stormrider","Thistledown","Thorncraft","Thornveil","Thornwhisper","Vexstar","Voidcaller","Voidfire","Windrider","Windstrider","Windwalker")
    val halfling_male_names = listOf("Abrutel","Agind","Ansus","Arees","Audgen","Aydeman","Ayden","Buric","Char","Chijn","Clast","Colon","Cored","Devon","Dris","Dylon","Elevan","Elvinus","Ercel","Evror","Frechus","Gier","Gouden","Guntoon","Hillun","Huck","Ichabod","Isaak","Jambul","Jarleon","Juregar","Kein","Leux","Lulf","Marlar","Merg","Nevon","Nornach","Oduin","Roeldul","Roman","Ruudon","Siclar","Silbert","Sjef","Stard","Sugis","Sundran","Tabor","Thett","Theun","Titust","Toonars","Trus","Twan","Tylen","Wald","Wark","Wildric","Willow","Zwenar")
    val halfling_female_names = listOf("Abecilia","Adene","Alia","Amaba","Amarra","Anca","Anda","Andina","Andra","Annata","Antixa","Arena","Armorra","Arrita","Arromina","Auska","Azuria","Baroneda","Bendra","Bria","Candretta","Cata","Cinobe","Crosa","Cuzena","Delina","Druga","Elga","Eluska","Emiana","Ezmia","Faunia","Filvana","Fiora","Gisana","Grea","Hena","Ilene","Katrieta","Lorea","Macchia","Manna","Maudika","Menega","Mina","Nemonea","Niconta","Nilora","Osta","Ostxoa","Pera","Pietsa","Rina","Rossenda","Uropasia","Vieria","Vita","Zanda","Zumika")
    val halfling_last_names = listOf("Bumbleberry","Burrow","Cavearen","Copperpine","Copperspark","Dell","Den","Endsinn","Glen","Goldenthorne","Greembanks","Greenbottle","Grove","Haven","Halfknot","Hilltop","Knoll","Meadowburrow","Meadowhopper","Nook","Oakthorn","Perch","Pits","Pitt","Rest","Row","Smallshadow","Stoop","Thicket","Thornfoot","Vale","Weathertoe","Willowsnest")
}
